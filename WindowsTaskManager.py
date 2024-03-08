import sys
import psutil
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import *
import os
import subprocess

class StyledPushButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f8f8f8;
                border: 1px solid #d8d8d8;
                padding: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)

class StyledLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("font-weight: bold;")

class ProcessDetailsWindow(QWidget):
    def __init__(self, pid):
        super().__init__()

        self.setWindowTitle(f"Process Details - PID: {pid}")
        self.setGeometry(200, 200, 800, 600)

        self.tab_widget = QTabWidget()

        # Tab for files
        file_tab = QWidget()
        file_layout = QVBoxLayout()

        self.file_list_widget = QListWidget()
        file_layout.addWidget(self.file_list_widget)

        delete_button = StyledPushButton("Delete Selected File")
        delete_button.clicked.connect(self.delete_selected_file)
        file_layout.addWidget(delete_button)

        file_tab.setLayout(file_layout)

        # Tab for libraries
        lib_tab = QWidget()
        lib_layout = QVBoxLayout()

        self.lib_list_widget = QListWidget()
        lib_layout.addWidget(self.lib_list_widget)

        lib_tab.setLayout(lib_layout)

        # Add tabs to the tab widget
        self.tab_widget.addTab(file_tab, "Files")
        self.tab_widget.addTab(lib_tab, "Libraries")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        self.pid = pid

        # Load initial data
        self.update_files_tab()
        self.update_libraries_tab()

    def update_files_tab(self):
        self.file_list_widget.clear()

        try:
            files = [f.path for f in psutil.Process(self.pid).open_files()]

            for file in files:
                self.file_list_widget.addItem(file)
        except Exception as e:
            print(f"An error occurred while updating files tab: {e}")

    def update_libraries_tab(self):
        self.lib_list_widget.clear()

        try:
            libs = [lib for lib in psutil.Process(self.pid).memory_maps()]

            for lib in libs:
                self.lib_list_widget.addItem(lib.path)
        except psutil.AccessDenied:
            print(f"Access denied. Unable to retrieve information for PID {self.pid}.")
        except Exception as e:
            print(f"An error occurred while updating libraries tab: {e}")

    def delete_selected_file(self):
        selected_item = self.file_list_widget.currentItem()
        if selected_item:
            file_path = selected_item.text()
            print(f"Deleting file: {file_path}")
            self.update_files_tab()

class PerformanceSummaryWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu_label = StyledLabel("CPU Usage:")
        self.cpu_usage_label = QLabel()

        self.memory_label = StyledLabel("Memory Usage:")
        self.memory_usage_label = QLabel()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.cpu_label)
        main_layout.addWidget(self.cpu_usage_label)
        main_layout.addWidget(self.memory_label)
        main_layout.addWidget(self.memory_usage_label)

        self.setLayout(main_layout)

        self.update_performance_summary()

    def update_performance_summary(self):
         cpu_percent_list = psutil.cpu_percent(percpu=True)
         avg_cpu_percent = sum(cpu_percent_list) / len(cpu_percent_list)
         memory_info = psutil.virtual_memory()

         self.cpu_usage_label.setText(f"{avg_cpu_percent:.2f}%")
         self.memory_usage_label.setText(f"Used: {memory_info.used / (1024 * 1024):.2f} MB, Total: {memory_info.total / (1024 * 1024):.2f} MB")
class TaskManagerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: white;")

        self.processes_button = StyledPushButton("Processes")
        self.services_button = StyledPushButton("Services")
        #self.performance_summary_button = StyledPushButton("Performance Summary")

        self.processes_button.clicked.connect(self.show_processes)
        self.services_button.clicked.connect(self.show_services)
     #   self.performance_summary_button.clicked.connect(self.show_performance_summary)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels(["PID/Service Name", "Name/Display Name", "Memory/Status", "CPU/Start Type",
                                                    "Local IP", "Local Port", "Remote IP", "Remote Port"])

        self.end_button = StyledPushButton("End Task/Stop Service")
        self.end_button.clicked.connect(self.end_task_or_service)

        self.performance_summary_widget = PerformanceSummaryWidget()

        self.layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.processes_button)
        button_layout.addWidget(self.services_button)
        #button_layout.addWidget(self.performance_summary_button)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.performance_summary_widget)
        self.layout.addWidget(self.table_widget)

        refresh_layout = QHBoxLayout()

        self.auto_refresh_checkbox = QCheckBox("Auto Refresh")
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        self.refresh_interval_input = QLineEdit(self)
        self.refresh_interval_input.setPlaceholderText("Refresh Interval (seconds)")
        self.refresh_interval_input.setValidator(QIntValidator())  # Only allow integer input

        refresh_layout.addWidget(self.auto_refresh_checkbox)
        refresh_layout.addWidget(self.refresh_interval_input)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)

        self.refresh_button = StyledPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        self.refresh_button.setFixedSize(80, 40)

        refresh_layout.addWidget(self.refresh_button)
        refresh_layout.addStretch()  # Add stretchable space to push buttons to the right
        refresh_layout.addWidget(self.end_button)
        self.layout.addLayout(refresh_layout)

        self.setLayout(self.layout)

        self.details_windows = {}

        self.show_processes()
        self.show_processes()
        self.table_widget.itemDoubleClicked.connect(self.show_process_details)

        for i in range(self.table_widget.columnCount()):
            self.table_widget.setSortingEnabled(True)
            self.table_widget.sortByColumn(i, Qt.AscendingOrder)

    def toggle_auto_refresh(self, state):
        if state == Qt.Checked:
            # Start the timer when the checkbox is checked
            refresh_interval = int(self.refresh_interval_input.text()) if self.refresh_interval_input.text() else 1
            self.refresh_timer.start(refresh_interval * 1000)  # Convert seconds to milliseconds
        else:
            # Stop the timer when the checkbox is unchecked
            self.refresh_timer.stop()

    def auto_refresh(self):
        if a == 1:
            self.show_processes()
            self.show_performance_summary()
        elif a == 2:
            self.show_services()
            self.show_performance_summary()

    def refresh_table(self):
        if a == 1:
            self.show_processes()
            self.show_performance_summary()
            #self.update_performance_summary()
        elif a == 2:
            self.show_services()
            self.show_performance_summary()

    def show_processes(self):
        global a
        a = 1
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels(["PID", "Name", "Memory", "CPU",
                                                    "Local IP", "Local Port", "Remote IP", "Remote Port"])
        self.table_widget.setRowCount(0)

        try:
            for process in psutil.process_iter(['pid', 'name', 'memory_info', 'connections', 'cpu_percent']):
                pid = process.info['pid']
                cpu_percent = process.info['cpu_percent']
                process_name = process.info['name']
                memory = process.info['memory_info'].rss / (1024 * 1024)
                
                #cpu_percent = process.cpu_percent(interval = 0.01) / psutil.cpu_count()
                #cpu_percent = process('cpu_percent')
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)
                self.table_widget.setItem(row_position, 0, QTableWidgetItem(str(pid)))
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(process_name))
                self.table_widget.setItem(row_position, 2, QTableWidgetItem(f"{memory:.2f} MB"))
                self.table_widget.setItem(row_position, 3, QTableWidgetItem(f"{cpu_percent:.2f}%"))
                

                connections = process.info.get('connections', [])
                for connection in connections:
                    if connection.laddr and connection.raddr:
                        local_ip, local_port = connection.laddr
                        remote_ip, remote_port = connection.raddr

                        self.table_widget.setItem(row_position, 4, QTableWidgetItem(local_ip))
                        self.table_widget.setItem(row_position, 5, QTableWidgetItem(str(local_port)))
                        self.table_widget.setItem(row_position, 6, QTableWidgetItem(remote_ip))
                        self.table_widget.setItem(row_position, 7, QTableWidgetItem(str(remote_port)))
        except Exception as e:
            print(f"An error occurred while updating the processes table: {e}")

        self.table_widget.itemDoubleClicked.connect(self.show_process_details)
        


    def show_process_details(self, item):
        pid = int(self.table_widget.item(item.row(), 0).text())

        try:
            if pid in self.details_windows:
                details_window = self.details_windows[pid]
                details_window.show()
            else:
                details_window = ProcessDetailsWindow(pid)
                self.details_windows[pid] = details_window

                details_window.destroyed.connect(lambda: self.details_windows.pop(pid, None))

                details_window.show()
        except Exception as e:
            print(f"An error occurred while showing process details: {e}")

    def end_task_or_service(self):
        selected_item = self.table_widget.currentItem()
        if selected_item:
            identifier = selected_item.text().split()[0]
            try:
                if identifier.isdigit():
                    pid = int(identifier)
                    psutil.Process(pid).terminate()
                    print(f"Terminated process with PID: {pid}")
                    self.show_processes()
                else:
                    #service_info = psutil.win_service_get(identifier)
                    #print(identifier)
                    #os.system("sc config " + identifier + " start=disabled")
                    os.system(f'net stop {identifier}')
                    #os.system(f'net stop {}')

                    
            except Exception as e:
                print(f"An error occurred while terminating the process/service: {e}")

                

    def show_services(self):
        global a
        a = 2
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Service Name", "Display Name", "Status", "Start Type"])
        self.table_widget.setRowCount(0)

        try:
            services = list(psutil.win_service_iter())
            for service in services:
                service_name = service.name()
                display_name = service.display_name()
                status = service.status()
                start_type = service.start_type()

                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)
                self.table_widget.setItem(row_position, 0, QTableWidgetItem(service_name))
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(display_name))
                self.table_widget.setItem(row_position, 2, QTableWidgetItem(status))
                self.table_widget.setItem(row_position, 3, QTableWidgetItem(start_type))
        except Exception as e:
            print(f"An error occurred while updating the services table: {e}")

    def stop_service(self):
        # Add your code here to stop the selected service
        pass

    def show_performance_summary(self):
            self.performance_summary_widget.update_performance_summary()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManagerApp()
    window.show()
    sys.exit(app.exec_())
