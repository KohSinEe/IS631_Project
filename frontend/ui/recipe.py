import streamlit as st
from services.inventory import fetch_inventory
from services.recipe import generate_recipe


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


def handle_generate_recipe():
    st.title("Generate recipe")

    if st.button("Back to Dashboard"):
        st.session_state.category_filter = "All"
        st.session_state.page = "dashboard"
        st.rerun()

    inventory = fetch_inventory()
    if not inventory:
        st.info("Your fridge is empty. Add some items first!")
        st.stop()

    with st.spinner("Generating recipes… 🍳 This may take a few seconds."):
        recipe = generate_recipe(inventory, 1, True, {})
    display_recipes(recipe)
