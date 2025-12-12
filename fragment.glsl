#version 330 core

in vec3 v_color;

out vec4 finalColor;

void main() {
    finalColor = vec4(v_color, 1.0);  // Cor da linha da cruz
}
