from OpenGL.GL import *
import numpy as np
import ctypes
import glm

class Block:
    def __init__(self, width, height, depth, colors, position, open_faces=None):
        self.position = position
        self.vao, self.count = self._generate(
            width, height, depth,
            colors["floor"], colors["wall"], colors["top"],
            open_faces
        )

    def _generate(self, width, height, depth, colorFloor, colorWall, colorTop, open_faces):
        if open_faces is None:
            open_faces = set()

        x, y, z = width/2, height/2, depth/2

        faces = [
            ([-x,-y,-z,  x,-y,-z,  x, y,-z,  x, y,-z, -x, y,-z, -x,-y,-z], colorWall),
            ([-x,-y, z,  x,-y, z,  x, y, z,  x, y, z, -x, y, z, -x,-y, z], colorWall),
            ([-x, y, z, -x, y,-z, -x,-y,-z, -x,-y,-z, -x,-y, z, -x, y, z], colorWall),
            ([ x, y, z,  x, y,-z,  x,-y,-z,  x,-y,-z,  x,-y, z,  x, y, z], colorWall),
            ([-x,-y,-z,  x,-y,-z,  x,-y, z,  x,-y, z, -x,-y, z, -x,-y,-z], colorFloor),
            ([-x, y,-z,  x, y,-z,  x, y, z,  x, y, z, -x, y, z, -x, y,-z], colorTop),
        ]

        vertices = []
        for idx, (coords, col) in enumerate(faces):
            if idx in open_faces:
                continue
            r, g, b = col
            for i in range(0, len(coords), 3):
                vertices += [coords[i], coords[i+1], coords[i+2], r, g, b]

        vertices = np.array(vertices, dtype=np.float32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        stride = 6 * 4
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)
        return vao, int(len(vertices) / 6)

    def draw(self, shader):
        glBindVertexArray(self.vao)
        model = glm.translate(glm.mat4(1), self.position)
        glUniformMatrix4fv(glGetUniformLocation(shader, "model"), 1, GL_FALSE, glm.value_ptr(model))
        glDrawArrays(GL_TRIANGLES, 0, self.count)
