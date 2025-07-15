# processing_context.py

class ProcessingContext:
    def __init__(self):
        self.current_file = 'none'
        self.current_line = 0

    def set_file_line(self, file_name, line_number):
        self.current_file = file_name
        self.current_line = line_number

    def location_str(self):
        return f"[On line {self.current_line} of {self.current_file} file.]"