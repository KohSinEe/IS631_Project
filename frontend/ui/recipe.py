import streamlit as st
from services.client import APIError
from services.inventory import fetch_inventory
from services.recipe import cook_recipe, generate_recipe
from state.session import mark_inventory_dirty


def display_recipes(result):
    if not result or "recipes" not in result:
        st.info("No recipes generated.")
        return

    for idx, recipe in enumerate(result["recipes"], 1):
        with st.expander(f"Recipe {idx}: {recipe['title']}"):
            if "time_minutes" in recipe:
                st.markdown(f"**Estimated Time**: {recipe['time_minutes']} minutes")

            st.markdown("### Ingredients")
            for ing in recipe.get("ingredients", []):
                st.write(f"- {ing}")

            missing = recipe.get("missing_ingredients", [])
            if missing:
                st.markdown("### Missing Ingredients (need to buy)")
                for ing in missing:
                    st.write(f"- {ing}")

            st.markdown("### Instructions")
            for step_idx, step in enumerate(recipe.get("steps", []), 1):
                st.write(f"{step_idx}. {step}")

            if "reason" in recipe:
                st.markdown(f"**Reason for this recipe:** {recipe['reason']}")

            if missing:
                st.warning("This recipe cannot be cooked yet because some ingredients are missing.")
            else:
                st.caption("Finished cooking? Click below to deduct the ingredients used.")
                if st.button("Cooked!", key=f"cook_{idx}"):
                    try:
                        cook_recipe(recipe)
                        st.session_state.flash_success = "Ingredients deducted from fridge."
                        st.session_state.category_filter = "All"
                        st.session_state.page = "dashboard"
                        mark_inventory_dirty(rerun=True)
                    except APIError as err:
                        st.error(f"Failed to deduct ingredients: {err}")


def handle_generate_recipe():
    st.title("Generate recipe")

    if st.button("Back to Dashboard"):
        st.session_state.category_filter = "All"
        st.session_state.page = "dashboard"
        st.rerun()

    inventory_only = st.session_state.get("inventory_only", True)
    use_household_allergens = st.session_state.get("use_household_allergens", False)

    inventory = fetch_inventory()
    if not inventory:
        st.info("Your fridge is empty. Add some items first!")
        st.stop()

    with st.spinner("Generating recipes…"):
        try:
            recipe = generate_recipe(
                inventory,
                max_recipes=3,
                inventory_only=inventory_only,
                preferences={},
                use_household_allergens=use_household_allergens,
            )
            display_recipes(recipe)

        except Exception as e:
            st.error(f"Failed to generate recipes: {e}")
