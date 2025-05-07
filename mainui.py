import sys
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QFileDialog, QTextEdit, QDialog, QLineEdit, 
                            QFormLayout, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        
        # Load current settings or use defaults
        self.settings = {
            'input_dir': os.path.expanduser('~/Pictures'),
            'output_dir': os.path.expanduser('~/Documents/TextRecognition')
        }
        
        # Try to load previous settings if they exist
        self.load_settings()
        
        # Create form layout
        layout = QFormLayout()
        
        # Input directory settings
        input_layout = QHBoxLayout()
        self.input_dir_edit = QLineEdit(self.settings['input_dir'])
        input_browse_btn = QPushButton("Browse...")
        input_browse_btn.clicked.connect(self.browse_input_dir)
        input_layout.addWidget(self.input_dir_edit)
        input_layout.addWidget(input_browse_btn)
        
        # Output directory settings
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings['output_dir'])
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(output_browse_btn)
        
        # Add to form layout
        layout.addRow("Input Images Directory:", input_layout)
        layout.addRow("Output Text Files Directory:", output_layout)
        
        # Add save/cancel buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        # Add all layouts to main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def browse_input_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Input Directory", self.input_dir_edit.text())
        if dir_path:
            self.input_dir_edit.setText(dir_path)
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir_edit.text())
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def save_settings(self):
        # Get values from input fields
        input_dir = self.input_dir_edit.text()
        output_dir = self.output_dir_edit.text()
        
        # Validate directories
        if not os.path.isdir(input_dir):
            QMessageBox.warning(self, "Invalid Directory", "Input directory does not exist!")
            return
            
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
                QMessageBox.information(self, "Directory Created", f"Created output directory: {output_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create output directory: {str(e)}")
                return
        
        # Save settings
        self.settings['input_dir'] = input_dir
        self.settings['output_dir'] = output_dir
        
        # Write settings to file
        try:
            config_dir = os.path.expanduser("~/.config/text_recognition")
            os.makedirs(config_dir, exist_ok=True)
            
            with open(os.path.join(config_dir, "settings.conf"), "w") as f:
                for key, value in self.settings.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            QMessageBox.warning(self, "Settings Warning", f"Could not save settings: {str(e)}")
        
        self.accept()
    
    def load_settings(self):
        try:
            config_file = os.path.expanduser("~/.config/text_recognition/settings.conf")
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            self.settings[key] = value
        except Exception:
            # If any error occurs, use default settings
            pass
    
    def get_settings(self):
        return self.settings


class TextRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window properties
        self.setWindowTitle("Text Recognition")
        self.setGeometry(100, 100, 800, 600)
        
        # Load settings
        self.settings_dialog = SettingsDialog(self)
        self.settings = self.settings_dialog.get_settings()
        
        # Selected image file
        self.selected_image = None
        
        # Create UI
        self.init_ui()
    
    def init_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Header section
        header_layout = QHBoxLayout()
        title_label = QLabel("Text Recognition")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label, 1)
        
        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        header_layout.addWidget(settings_button, 0)
        
        main_layout.addLayout(header_layout)
        
        # File selection section
        file_group = QGroupBox("Image Selection")
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setWordWrap(True)
        
        browse_button = QPushButton("Browse Images")
        browse_button.clicked.connect(self.browse_image)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_button, 0)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Results section
        results_group = QGroupBox("Recognition Results")
        results_layout = QVBoxLayout()
        
        # Text output area
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Text from image will appear here")
        
        results_layout.addWidget(self.result_text)
        
        # Run button
        self.run_button = QPushButton("Run Recognition")
        self.run_button.setEnabled(False)  # Disabled until an image is selected
        self.run_button.clicked.connect(self.run_recognition)
        
        # Add save button
        self.save_button = QPushButton("Save Text")
        self.save_button.setEnabled(False)  # Disabled until text is generated
        self.save_button.clicked.connect(self.save_text)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.save_button)
        
        results_layout.addLayout(button_layout)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # Status bar for messages
        self.statusBar().showMessage("Ready")
        
        # Finalize UI
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def open_settings(self):
        if self.settings_dialog.exec_():
            self.settings = self.settings_dialog.get_settings()
            self.statusBar().showMessage("Settings updated", 3000)
    
    def browse_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image File", 
            self.settings['input_dir'],
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)", 
            options=options
        )
        
        if file_path:
            self.selected_image = file_path
            self.file_path_label.setText(file_path)
            self.run_button.setEnabled(True)
            self.statusBar().showMessage(f"Selected: {os.path.basename(file_path)}", 3000)
    
    def run_recognition(self):
        if not self.selected_image:
            QMessageBox.warning(self, "Error", "Please select an image first.")
            return
        
        # Placeholder: Generate Lorem Ipsum text
        # In a real app, this would call the OCR logic
        self.statusBar().showMessage("Processing image...", 2000)
        
        # Generate random lorem ipsum paragraphs
        lorem_paragraphs = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam in dui mauris. Vivamus hendrerit arcu sed erat molestie vehicula. Sed auctor neque eu tellus rhoncus ut eleifend nibh porttitor.",
            "Ut in nulla enim. Phasellus molestie magna non est bibendum non venenatis nisl tempor. Suspendisse dictum feugiat nisl ut dapibus. Mauris iaculis porttitor posuere.",
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
            "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt."
        ]
        
        # Select 1-4 paragraphs randomly
        num_paragraphs = random.randint(1, 4)
        selected_paragraphs = random.sample(lorem_paragraphs, num_paragraphs)
        
        # Set text in result area
        self.result_text.clear()
        self.result_text.setText("\n\n".join(selected_paragraphs))
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        self.statusBar().showMessage("Recognition complete", 3000)
    
    def save_text(self):
        # Get the text from the result area
        text = self.result_text.toPlainText()
        
        if not text:
            QMessageBox.warning(self, "Error", "No text to save.")
            return
        
        # Create a default filename based on the image name
        if self.selected_image:
            base_name = os.path.splitext(os.path.basename(self.selected_image))[0]
            default_path = os.path.join(self.settings['output_dir'], f"{base_name}.txt")
        else:
            default_path = os.path.join(self.settings['output_dir'], "recognized_text.txt")
        
        # Ask where to save the file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text File",
            default_path,
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        
        if file_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write to file
                with open(file_path, 'w') as f:
                    f.write(text)
                
                self.statusBar().showMessage(f"Saved to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform look
    window = TextRecognitionApp()
    window.show()
    sys.exit(app.exec_())