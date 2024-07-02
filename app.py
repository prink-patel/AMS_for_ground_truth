import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pandas as pd

class DrawableRectItem(QGraphicsRectItem):
    def __init__(self, rect, color=Qt.red, parent=None):
        super().__init__(rect, parent)
        self.is_created = False
        self.is_correct = False
        self.color = color
        self.setPen(QPen(self.color, 2, Qt.SolidLine))

    def toggle_color(self):
        self.is_correct = not self.is_correct
        self.setPen(QPen(Qt.green if self.is_correct else Qt.red, 2, Qt.SolidLine))
        
        if self.is_correct:
            rect = self.rect()
            x = rect.x()
            y = rect.y()
            width = rect.width()
            height = rect.height()
            print(f"Clicked ROI: x={x}, y={y}, width={width}, height={height}")


class ClickableLabel(QGraphicsView):
    def __init__(self, image_viewer, parent=None):
        super().__init__(parent)
        self.image_viewer = image_viewer
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.rois = []
        self.df_row = None
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.drawing_mode = False
        self.current_rect = None

        # Initialize default rectangle
        default_rect = QRectF(100, 100, 200, 150)  # Example coordinates
        self.default_rect_item = DrawableRectItem(default_rect)
        self.scene.addItem(self.default_rect_item)

    def set_rois(self, rois, df_row):
        self.rois = rois
        self.df_row = df_row

    def setDrawingMode(self, mode):
        self.drawing_mode = mode

    def mousePressEvent(self, event):
        scene_event = self.mapToScene(event.pos())
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = scene_event
            self.current_rect = DrawableRectItem(QRectF(self.start_point, self.start_point))
            self.scene.addItem(self.current_rect)
        else:
            item = self.scene.itemAt(scene_event, QTransform())
            if isinstance(item, DrawableRectItem):
                print("correct")
                rect = item.rect()
                x = rect.x()
                y = rect.y()
                width = rect.width()
                height = rect.height()
                self.image_viewer.remove_selected_roi(x, y, width, height)
                
                item.toggle_color()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = self.mapToScene(event.pos())
            self.current_rect.setRect(QRectF(self.start_point, self.end_point))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing and event.button() == Qt.LeftButton:
            self.drawing = False
            self.end_point = self.mapToScene(event.pos())
            self.current_rect.setRect(QRectF(self.start_point, self.end_point))
            self.current_rect.is_created = True
            self.image_viewer.saveRectangle(self.start_point, self.end_point)
        super().mouseReleaseEvent(event)

    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        resized_pixmap = pixmap.scaled(800,900, Qt.KeepAspectRatioByExpanding)
        self.scene.clear()
        self.scene.addPixmap(resized_pixmap)
        print(self.scene.sceneRect().size())
        
        self.setSceneRect(QRectF(pixmap.rect()))
        self.rois = []
        self.df_row = None

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = pd.read_csv("labels_het.csv")
        self.save_df = pd.read_csv("demo.csv")
        self.new_df = pd.DataFrame(columns=["image_name", "class", "x", "y", "width", "height", "confidence"])
        self.setWindowTitle('Image Viewer')
        self.imagePaths = []
        self.currentImageIndex = 0
        self.initUI()
        self.shortcut_event()
        self.final_image_width=1920
        self.final_image_height=1080

    def shortcut_event(self):
        self.next_button_shortcut = QShortcut(QKeySequence("right"), self)
        self.next_button_shortcut.activated.connect(self.nextImage)
        self.previous_button_shortcut = QShortcut(QKeySequence("left"), self)
        self.previous_button_shortcut.activated.connect(self.prevImage)
        self.drawing_shortcut = QShortcut(QKeySequence("1"), self)
        self.drawing_shortcut.activated.connect(self.toggleDrawingMode)
    
    def toggleDrawingMode(self):
        self.label.setDrawingMode(not self.label.drawing_mode)
        if self.label.drawing_mode:
            QApplication.setOverrideCursor(Qt.CrossCursor)
            print("Drawing mode activated")
        else:
            print("Drawing mode deactivated")

    def initUI(self):
        self.centralWidget = QWidget()
        self.layout = QVBoxLayout()
        self.label = ClickableLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.nextButton = QPushButton('Next')
        self.prevButton = QPushButton('Previous')
        self.folderButton = QPushButton('Select Folder')
        self.folderButton.clicked.connect(self.selectFolder)
        self.nextButton.clicked.connect(self.nextImage)
        self.prevButton.clicked.connect(self.prevImage)
        self.layout.addWidget(self.folderButton)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.nextButton)
        self.layout.addWidget(self.prevButton)
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    def selectFolder(self):
        # folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        # if folder_path:
            # self.loadImages(folder_path)
        if True:
            self.loadImages("/home/wot-prink/Documents/desktop/ams_for_ground_truth/images_1")

    def loadImages(self, folder_path):
        self.imagePaths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        self.imagePaths.sort()
        self.currentImageIndex = 0
        self.updateImage()

    def updateImage(self):
        if self.imagePaths:

            if self.imagePaths[self.currentImageIndex].split("/")[-1] in self.save_df["image_name"].values:
                print("innercondition",self.currentImageIndex)
                self.currentImageIndex += 1
                self.updateImage()
            self.label.display_image(self.imagePaths[self.currentImageIndex])
            self.image_width, self.image_height = self.label.scene.sceneRect().size().width(), self.label.scene.sceneRect().size().height()

            self.image_name = os.path.basename(self.imagePaths[self.currentImageIndex])
            self.df_row = self.df[self.df["image_name"] == self.image_name].copy()
            if not self.df_row.empty:
                for i in range(len(self.df_row)):
                    print(self.df_row.iloc[i])
                    x=float(self.df_row.iloc[i]["x"])*self.image_width
                    y=float(self.df_row.iloc[i]["y"])*self.image_height
                    width=float(self.df_row.iloc[i]["width"])*self.image_width
                    height=float(self.df_row.iloc[i]["height"])*self.image_height
                    x1=x-(width/2)
                    y1=y-(height/2)
                    
                    rect = QRectF(x1,y1,width,height)
                    print(rect)
                    roi_item = DrawableRectItem(rect)
                    self.label.scene.addItem(roi_item)
                    self.label.rois.append(roi_item)
                self.label.set_rois(self.label.rois, self.df_row)
            else:
                self.label.set_rois([], None)

    def saveRectangle(self, start_point, end_point):
        x = min(start_point.x(), end_point.x())
        y = min(start_point.y(), end_point.y())
        width = abs(start_point.x() - end_point.x())
        height = abs(start_point.y() - end_point.y())
        # print(f"x: {x}, y: {y}, width: {width}, height: {height}")

        new_data = {
            "image_name": self.image_name,
            "class": 0,
            "x": (x+(width/2)) / self.image_width,
            "y": (y+(height/2)) / self.image_height, 
            "width": width / self.image_width,
            "height": height / self.image_height,
            "confidence": 0.0
        }
        self.df_row = self.df_row._append(new_data, ignore_index=True)
        self.df_row.to_csv("phone_GT_h.csv", index=False)

    def saveSelection(self):
        if not self.df_row.empty:
            for i in range(len(self.df_row)):
                row_to_add = {
                    "image_name": self.image_name,
                    "class": int(self.df_row.iloc[i]["class"]),
                    "x": float(self.df_row.iloc[i]["x"]),
                    "y": float(self.df_row.iloc[i]["y"]),
                    "width": float(self.df_row.iloc[i]["width"]),
                    "height": float(self.df_row.iloc[i]["height"]),
                    "confidence": float(self.df_row.iloc[i]["confidence"])
                }
                
                # df = df.append(row_to_add, ignore_index=True)
                # print(row_to_add)
                self.new_df = self.new_df._append(row_to_add, ignore_index=True)
            self.new_df.to_csv("phone_GT_h.csv", index=False)

    def removeSelection(self):
        self.new_df = self.new_df[self.new_df['image_name'] != self.image_name]
        
        self.new_df.to_csv("phone_GT_h.csv", index=False)
        
        



    def remove_selected_roi(self,x,y,width,height):
        
        print(x/self.image_width, y/self.image_height, width, height)

        
        scaled_x = x / self.image_width
        scaled_y = y / self.image_height
        width = width / self.image_width
        height = height / self.image_height
        
        
        scaled_x = scaled_x+(width/2)
        scaled_y = scaled_y+(height/2)
        
        
        scaled_x = round(scaled_x, 6)
        scaled_y = round(scaled_y, 6)
        scaled_width = round(width, 6)
        scaled_height = round(height, 6)
        
        print("df_row")
        print(self.df_row)
        print("values")
        print(scaled_x, scaled_y, scaled_width, scaled_height)
        
        criteria = (
            (round(self.df_row["x"],6) == scaled_x) &
            (round(self.df_row["y"],6) == scaled_y) 
            (round(self.df_row["width"],6) == scaled_width) &
            (round(self.df_row["height"],6) == scaled_height)
        )
        print(criteria)
        # Filter out rows based on criteria
        self.df_row = self.df_row[~criteria].reset_index(drop=True)
        print("Filtered df_row:")
        print(self.df_row)
        print("Filtered df_row:")

    def toggleDrawingMode(self):
        self.label.setDrawingMode(not self.label.drawing_mode)
        if self.label.drawing_mode:
            print("Drawing mode activated")
        else:
            print("Drawing mode deactivated")
        
        

    def nextImage(self):
        self.saveSelection()
        self.currentImageIndex += 1
        if self.currentImageIndex >= len(self.imagePaths):
            self.currentImageIndex = 0
        self.updateImage()

    def prevImage(self):
        self.currentImageIndex -= 1
        if self.currentImageIndex < 0:
            self.currentImageIndex = len(self.imagePaths) - 1
        self.updateImage()

if __name__ == '__main__':
    app = QApplication([])
    viewer = ImageViewer()
    viewer.show()
    app.exec_()
