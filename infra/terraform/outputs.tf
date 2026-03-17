output "instance_id" {
  value = aws_instance.demo.id
}

output "public_ip" {
  value = aws_instance.demo.public_ip
}

output "streamlit_url" {
  value = "http://${aws_instance.demo.public_ip}:8501"
}

output "api_url" {
  value = "http://${aws_instance.demo.public_ip}:8000/docs"
}
