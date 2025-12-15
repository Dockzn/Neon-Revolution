import glm
import glfw

class Camera:
    def __init__(self):
        self.position = glm.vec3(0, 2, 5)
        self.front = glm.vec3(0, 0, -1)
        self.up = glm.vec3(0, 1, 0)

        self.yaw = -90.0
        self.pitch = 0.0

        self.lastX = 400
        self.lastY = 300
        self.firstMouse = True

    def process_mouse(self, xpos, ypos):
        if self.firstMouse:
            self.lastX = xpos
            self.lastY = ypos
            self.firstMouse = False

        xoffset = xpos - self.lastX
        yoffset = self.lastY - ypos
        self.lastX = xpos
        self.lastY = ypos

        sensitivity = 0.1
        self.yaw += xoffset * sensitivity
        self.pitch += yoffset * sensitivity
        self.pitch = max(-89, min(89, self.pitch))

        direction = glm.vec3(
            glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch)),
            glm.sin(glm.radians(self.pitch)),
            glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        )
        self.front = glm.normalize(direction)

    def process_keyboard(self, window, deltaTime):
        speed = 3 * deltaTime
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.position += self.front * speed
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.position -= self.front * speed
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            self.position -= glm.normalize(glm.cross(self.front, self.up)) * speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            self.position += glm.normalize(glm.cross(self.front, self.up)) * speed
