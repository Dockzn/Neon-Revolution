import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders as gls
import glm

from camera import Camera
from block import Block

class Game:
    def __init__(self):
        self.width, self.height = 800, 600
        self.deltaTime = 0
        self.lastFrame = 0

        glfw.init()
        self.window = glfw.create_window(self.width, self.height, "Neon Revolution", None, None)
        glfw.make_context_current(self.window)

        glEnable(GL_DEPTH_TEST)

        self.camera = Camera()
        glfw.set_cursor_pos_callback(self.window, self.mouse_callback)
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        self.shader = self.load_shader()
        self.blocks = self.create_scene()

    def mouse_callback(self, window, xpos, ypos):
        self.camera.process_mouse(xpos, ypos)

    def load_shader(self):
        with open("vertex.glsl") as f:
            vs = f.read()
        with open("fragment.glsl") as f:
            fs = f.read()
        return gls.compileProgram(
            gls.compileShader(vs, GL_VERTEX_SHADER),
            gls.compileShader(fs, GL_FRAGMENT_SHADER)
        )

    def create_scene(self):
        colors = {
            "floor": (0.2, 0.2, 0.3),
            "wall":  (0.8, 0.1, 0.4),
            "top":   (0.3, 0.3, 0.4)
        }

        return [
            Block(8, 1, 8, colors, glm.vec3(-10, 0, 0), open_faces={3}),
            Block(8, 1, 8, colors, glm.vec3(10, 0, 0), open_faces={2}),
            Block(20, 1, 6, colors, glm.vec3(0, 0, 0), open_faces={0, 1})
        ]

    def run(self):
        while not glfw.window_should_close(self.window):
            current = glfw.get_time()
            self.deltaTime = current - self.lastFrame
            self.lastFrame = current

            glfw.poll_events()
            self.camera.process_keyboard(self.window, self.deltaTime)

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.shader)

            view = glm.lookAt(self.camera.position, self.camera.position + self.camera.front, self.camera.up)
            proj = glm.perspective(glm.radians(60), self.width/self.height, 0.1, 200)

            glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
            glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))

            for block in self.blocks:
                block.draw(self.shader)

            glfw.swap_buffers(self.window)

        glfw.terminate()

if __name__ == "__main__":
    Game().run()
