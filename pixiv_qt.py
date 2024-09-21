import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem
)
from PyQt5.QtGui import QPixmap, QPainter, QWheelEvent
from PyQt5.QtCore import Qt
from PIL import Image


class ImageMerger(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.images = []
        self.merged_image = None  # 保存合并后的图像

    def initUI(self):
        self.setWindowTitle('壁纸合成工具')

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧布局
        left_layout = QVBoxLayout()

        # 添加图片按钮
        self.addButton = QPushButton('添加图片')
        self.addButton.clicked.connect(self.addImages)
        left_layout.addWidget(self.addButton)

        # 图片列表
        self.imageList = QListWidget()
        left_layout.addWidget(self.imageList)

        # 上移和下移按钮
        self.moveUpButton = QPushButton('上移')
        self.moveUpButton.clicked.connect(self.moveUp)
        left_layout.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton('下移')
        self.moveDownButton.clicked.connect(self.moveDown)
        left_layout.addWidget(self.moveDownButton)

        # 合并按钮
        # self.mergeButton = QPushButton('合并图片')
        # self.mergeButton.clicked.connect(self.mergeImages)
        # left_layout.addWidget(self.mergeButton)

        # 保存按钮
        self.saveButton = QPushButton('保存合并后的图片')
        self.saveButton.clicked.connect(self.saveMergedImage)
        left_layout.addWidget(self.saveButton)

        # 添加左侧布局到主布局，并设置比例
        main_layout.addLayout(left_layout, 1)  # 左侧

        # 右侧可视化编辑区域
        self.graphicsView = ImageViewer()
        main_layout.addWidget(self.graphicsView, 4)  # 右侧

        self.setLayout(main_layout)
    def addImages(self):
        files, _ = QFileDialog.getOpenFileNames(self, '选择图片', '', 'Images (*.png *.jpg *.jpeg)')
        if files:
            for file in files:
                try:
                    # 打开图片文件
                    img = Image.open(file)
                    self.images.append(file)
                    self.imageList.addItem(file)
                    self.updatePreview(img)  # 添加后更新预览
                except Exception as e:
                    print(f"无法添加图片 {file}: {e}")

    def updatePreview(self, img):
        """更新预览图"""
        self.mergeImages()  # 每次添加图片后合并并显示预览

    def moveUp(self):
        current_row = self.imageList.currentRow()
        if current_row > 0:
            # 交换当前项与上一个项
            self.images[current_row], self.images[current_row - 1] = self.images[current_row - 1], self.images[current_row]
            self.imageList.insertItem(current_row - 1, self.imageList.takeItem(current_row))
            self.imageList.setCurrentRow(current_row - 1)
            self.updatePreview(None)  # 更新预览

    def moveDown(self):
        current_row = self.imageList.currentRow()
        if current_row < len(self.images) - 1:
            # 交换当前项与下一个项
            self.images[current_row], self.images[current_row + 1] = self.images[current_row + 1], self.images[current_row]
            self.imageList.insertItem(current_row + 1, self.imageList.takeItem(current_row))
            self.imageList.setCurrentRow(current_row + 1)
            self.updatePreview(None)  # 更新预览

    def mergeImages(self):
        if not self.images:
            return

        # 获取最大高度
        max_height = 0
        img_sizes = []

        for img_path in self.images:
            try:
                img = Image.open(img_path)
                img_sizes.append((img_path, img.size))
                if img.height > max_height:
                    max_height = img.height
            except Exception as e:
                print(f"无法处理图片 {img_path}: {e}")

        img_list = []
        total_width = 0

        for img_path, (width, height) in img_sizes:
            try:
                img = Image.open(img_path)
                aspect_ratio = width / height
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                img_list.append(img)
                total_width += new_width
            except Exception as e:
                print(f"无法处理图片 {img_path}: {e}")

        # 创建合并后的图像
        self.merged_image = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for img in img_list:
            self.merged_image.paste(img, (x_offset, 0))
            x_offset += img.width

        # 在可视化区域显示合并后的图像
        self.displayMergedImage(self.merged_image)

    def displayMergedImage(self, img):
        """在可视化区域显示合并后的图片"""
        img.save("temp_image.png")  # 保存临时文件以便加载
        self.graphicsView.setImage(QPixmap("temp_image.png"))

    def saveMergedImage(self):
        """保存合并后的图像"""
        if self.merged_image is not None:
            output_path, _ = QFileDialog.getSaveFileName(self, '保存合并后的图片', '', 'PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)')
            if output_path:
                self.merged_image.save(output_path)
                print("合并后的图片已保存为:", output_path)
        else:
            print("没有合并后的图片可供保存。")


class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        self.scale_factor = 1.0
        self.is_dragging = False
        self.last_pos = None

    def setImage(self, pixmap):
        """设置要显示的图片"""
        self.scene.clear()
        item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(item)
        self.setSceneRect(item.boundingRect())
        self.fitInView(item, Qt.KeepAspectRatio)  # 自适应显示

    def wheelEvent(self, event: QWheelEvent):
        """处理鼠标滚轮事件以实现缩放"""
        factor = 1.2
        if event.angleDelta().y() < 0:
            factor = 1 / factor

        self.scale(factor, factor)  # 按照缩放因子缩放视图

    def mousePressEvent(self, event):
        """处理鼠标按下事件以开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件以实现拖拽"""
        if self.is_dragging:
            delta = event.pos() - self.last_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件以结束拖拽"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageMerger()
    ex.resize(800, 600)
    ex.show()
    sys.exit(app.exec_())
