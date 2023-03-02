import json
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog, messagebox
from tkinter import ttk
from typing import Union, List

import numpy as np
import pandas as pd

import utils
import sammon

BASE_DIR = os.getcwd()


def load_json(filepath: str) -> Union[pd.DataFrame, None]:
    """
    Ładowanie pliku json
    """
    with open(filepath, 'r', encoding="latin-1") as f:
        json_dict = json.load(f)
    json_dict = json_dict["feeds"]
    return json_dict


def load_text(filepath: str, delimiter: str) -> List[List[str]]:
    """
    Wczytywanie pliku txt z możliwością wyboru separatora
    """
    if delimiter == "":
        delimiter = None
    with open(filepath, 'r', encoding="latin-1") as f:
        text_list = f.read().splitlines()

    text_list = [line.split(delimiter) for line in text_list]
    return text_list


class DialogWindow(tk.Toplevel):
    def __init__(self, parent, choices: List, display_label: str, title: str):
        super().__init__(parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        self.display_label = display_label
        self.choices = choices
        self.body()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def body(self):
        w = 200
        h = 100
        ws = self.parent.winfo_screenwidth()
        hs = self.parent.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))

        # tzw. body okna dialogowego
        self.label = ttk.Label(self, text=self.display_label)
        self.label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.column_list = ttk.Combobox(self, values=self.choices, state="readonly")
        self.column_list.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.column_list.current(0)

        self.button_ok = ttk.Button(self, text="OK", command=self.ok)
        self.button_ok.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.button_cancel = ttk.Button(self, text="Cancel", command=self.cancel)
        self.button_cancel.grid(row=2, column=1, padx=5, pady=5, sticky="e")

        self.configure_grids()

    def ok(self):
        self.result = self.column_list.get()
        self.destroy()

    def cancel(self):
        self.destroy()

    def get_column_name(self) -> str:
        return self.result

    def configure_grids(self):
        rows = self.grid_size()[0]
        columns = self.grid_size()[1]
        for row in range(rows):
            for column in range(columns):
                self.grid_columnconfigure(column, weight=1)


class AcceptPCAInputs(tk.Toplevel):
    def __init__(self, parent, title: str, data, columns: List):
        super().__init__(parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        self.data = data
        self.columns = columns
        parent.eval(f'tk::PlaceWindow {str(self)} center')
        self.body()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def body(self):
        w = 800
        h = 400
        ws = self.parent.winfo_screenwidth()
        hs = self.parent.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))

        # górna ramka
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # środkowa ramka
        self.middle_frame = ttk.Frame(self)
        self.middle_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # dolna ramka
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # widgety na górną ramke
        _text = "Select the number of components to use:"
        self.label = ttk.Label(self.top_frame, text=_text)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # spinbox dla liczby głównych składowych
        self.spinbox = ttk.Spinbox(self.top_frame, from_=1, to=10, width=3)
        self.spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # widgety na środkową ramke
        _text = "Select the target column:"
        self.label = ttk.Label(self.middle_frame, text=_text)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # combobox for the target column
        self.column_list = ttk.Combobox(self.middle_frame, values=self.columns, state="readonly")
        self.column_list.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.column_list.current(0)

        # przyciski OK i anuluj
        self.button_ok = ttk.Button(self.bottom_frame, text="OK", command=self.ok)
        self.button_ok.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.button_cancel = ttk.Button(self.bottom_frame, text="Cancel", command=self.cancel)
        self.button_cancel.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.column_list.focus()

    def ok(self):
        target_column = self.column_list.get()
        n_components = self.spinbox.get()
        self.result = (target_column, n_components)
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

    def get_result(self):
        return self.result


class MainApplication(tk.Tk):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.data = None

        self.init_ui()

        frames = [self,
                  self.top_frame,
                  self.top_left_frame,
                  self.top_middle_frame,
                  self.top_right_frame,
                  self.body_frame,
                  self.body_left_frame]

        for frame in frames:
            self.do_grid_configurations(frame)

    def init_ui(self):
        self.config = utils.Config("config.txt")
        self.title("Main Application")
        # kształt okna
        w = 800
        h = 600
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))

        # górna ramka na przyciski
        self.top_frame = tk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)

        # przyciski
        self.add_buttons()
        # kolory
        self.add_colors()
        # środkowa ramka na tabele
        self.create_table()

        # dolna ramka do wyświetlania
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.grid(row=1, column=0, sticky="swe", padx=5, pady=5)
        self.add_display_labels()

    def add_display_labels(self):
        self.label_show_calculations = tk.Label(self.bottom_frame, text="")
        self.label_show_calculations.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.label_show_calculations.config(font=("Courier", 12))

    def add_buttons(self):
        # dodanie przycisków
        # load export
        self.top_left_frame = tk.Frame(self.top_frame)
        self.top_left_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)
        self.button_load_data = ttk.Button(self.top_left_frame, text="Load Data", command=self.load_data)
        self.button_load_data.grid(row=0, column=0)

        self.button_export_data = ttk.Button(self.top_left_frame, text="Export Data", command=self.export_data)
        self.button_export_data.grid(row=0, column=1)

        self.top_middle_frame = tk.Frame(self.top_frame)
        self.top_middle_frame.grid(row=0, column=1, sticky="new", padx=5, pady=5)
        # przyciski avg, med, stdev
        self.button_avg = ttk.Button(self.top_middle_frame, text="Avg", command=self.avg)
        self.button_avg.grid(row=0, column=0)

        self.button_med = ttk.Button(self.top_middle_frame, text="Med", command=self.med)
        self.button_med.grid(row=0, column=1)

        self.button_stdev = ttk.Button(self.top_middle_frame, text="Stdev", command=self.stdev)
        self.button_stdev.grid(row=0, column=2)

        self.top_right_frame = tk.Frame(self.top_frame)
        self.top_right_frame.grid(row=0, column=2, sticky="new", padx=5, pady=5)

        # przyciski PCA, Sammon
        self.button_pca = ttk.Button(self.top_right_frame, text="PCA", command=self.get_pca)
        self.button_pca.grid(row=0, column=0)

        self.button_sammon = ttk.Button(self.top_right_frame, text="Sammon", command=self.sammon)
        self.button_sammon.grid(row=0, column=1)

    def add_colors(self):
        
        pass

    def create_table(self):
        """
        implementacja tkintera
        :return:
        """
        self.body_frame = tk.Frame(self)
        self.body_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=5)

        self.body_left_frame = tk.Frame(self.body_frame)
        self.body_left_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        # pionowy scroll
        scrollbar = tk.Scrollbar(self.body_left_frame)
        scrollbar.pack(side="right", fill="y")
        # poziomy scroll
        scrollbar2 = tk.Scrollbar(self.body_left_frame, orient="horizontal")
        scrollbar2.pack(side="bottom", fill="x")

        # create table
        self.treeview = ttk.Treeview(self.body_left_frame, xscrollcommand=scrollbar2.set, yscrollcommand=scrollbar.set)

        scrollbar.config(command=self.treeview.yview)
        scrollbar2.config(command=self.treeview.xview)

        self.treeview.pack(fill="both", expand=True)  # wypełnienie w obu kierunkach
        self.treeview.config(height=20)

    def show_data(self):
        """
        pokazanie danych w tabeli
        :return:
        """
        # czyszczenie tabeli
        self.treeview.delete(*self.treeview.get_children())
        # dodanie danych do tabeli

        # ----- konfig kolumn -----
        # ustawienie nazw kolumn
        headers = self.data.columns.values.tolist()
        self.treeview["columns"] = headers
        self.treeview.column("#0", stretch=tk.NO, width=0, anchor="center")
        self.treeview.heading("#0", text="", anchor="center")
        # ust szerokosci kolumn
        for i in range(len(headers)):
            header_text = headers[i]
            self.treeview.column(header_text, anchor="center", width=100)
            self.treeview.heading(header_text, text=headers[i], anchor="center")

        # insert data into table
        for row in self.data.iterrows():
            self.treeview.insert("", "end", values=row[1].tolist())

    @staticmethod
    def do_grid_configurations(frame: Union[tk.Frame, tk.Tk]):
        # siatka
        # liczba wierszy w siatce
        num_rows = frame.grid_size()[1]
        # liczba kolumn
        num_columns = frame.grid_size()[0]
        for i in range(0, num_rows):
            frame.rowconfigure(i, weight=1)
        for i in range(0, num_columns):
            frame.columnconfigure(i, weight=1)

    # przypisanie funkcji do przycisków
    def load_data(self):
        data_loaded = False
        recent_dir = os.path.dirname(self.config.get("recent_file_path"))
        # okno dialogowe do wczytania plików
        self.file_path = filedialog.askopenfilename(initialdir=recent_dir, title="Select file",
                                                    filetypes=(("csv files", "*.csv"), ("json files", "*.json"),
                                                               ("Text files", "*.txt")))
        # wczytanie wybranego typu plku
        if self.file_path.endswith(".csv"):
            self.data = pd.read_csv(self.file_path, encoding="latin-1")
            data_loaded = True
        elif self.file_path.endswith(".json"):
            self.data = pd.DataFrame(load_json(self.file_path))
            data_loaded = True
        elif self.file_path.endswith(".txt"):
            # okno dialogowe do wyboru separatora
            delimiter = simpledialog.askstring(title="Select delimiter",
                                               prompt="Enter delimiter:", initialvalue=",", parent=self)
            # wczytanie zawartosci pliku
            # plik txt z separatorem
            text_list = load_text(self.file_path, delimiter)
            self.data = pd.DataFrame(text_list[1:], columns=text_list[0])

            for col in self.data.columns:  # konwersja danych na typ numerycny
                self.data[col] = pd.to_numeric(self.data[col], errors="ignore")
            data_loaded = True

        if data_loaded:
            self.config.set("recent_file_path", self.file_path)
            self.config.save()
            # pokazanie danych w tabeli
            self.show_data()

    def export_data(self):
        """
        eksport danych do csv
        :return:
        """
        if not isinstance(self.data, pd.DataFrame):
            return
        # otwarcie okna dialogowego
        typeVar = tk.StringVar()
        file_path = filedialog.asksaveasfilename(initialdir=os.path.dirname(self.config.get("recent_file_path")),
                                                 title="Save file",
                                                 filetypes=(("csv files", "*.csv"),
                                                            ("json files", "*.json"),
                                                            ("Text files", "*.txt")),
                                                 typevariable=typeVar)
        print(file_path)
        print(typeVar.get())
        if not file_path:
            return
        save_flag = False
        # eksport danych do pliku
        if typeVar.get() == "csv files":
            if not file_path.endswith(".csv"):
                file_path += ".csv"
            self.data.to_csv(file_path, index=False)
            save_flag = True
        elif typeVar.get() == "json files":
            if not file_path.endswith(".json"):
                file_path += ".json"
            self.data.to_json(file_path, orient="records")
            save_flag = True
        elif typeVar.get() == "Text files":
            if not file_path.endswith(".txt"):
                file_path += ".txt"
            self.data.to_csv(file_path, index=False, sep="\t")
            save_flag = True

        if save_flag:
            print(f"Data exported to file: {file_path}")
            self.config.set("recent_file_path", file_path)
            self.config.save()

    def avg(self):
        """
        Wybór kolumny do obliczenia średniej
        :return:
        """
        if isinstance(self.data, pd.DataFrame):
            # pobranie nazwy kolumny
            numerical_columns = utils.get_numerical_columns(self.data)
            if not numerical_columns:
                messagebox.showwarning("No numerical columns", "No numerical columns found in the data", parent=self)
                return
            dialog_window = DialogWindow(self, numerical_columns, "Select column to find average",
                                         "Select a numerical column")
            # pobranie nazwy kolumny
            column_name = dialog_window.get_column_name()
            if not column_name:
                return

            # obliczenie średniej
            avg = utils.get_average(self.data, column_name)

            # pokazanie średniej
            self.label_show_calculations.config(text=f"Average of {column_name} is {avg}")

    def med(self):
        """
        Wybór kolumny do obliczenia odchylenia standardowego
        :return:
        """
        if isinstance(self.data, pd.DataFrame):
            # pobranie nazwy kolumny
            numerical_columns = utils.get_numerical_columns(self.data)
            if not numerical_columns:
                messagebox.showwarning("No numerical columns", "No numerical columns found in the data", parent=self)
                return
            dialog_window = DialogWindow(self, numerical_columns, "Select column to find median",
                                         "Select a numerical column")
            # pobranie nazwy kolumny
            column_name = dialog_window.get_column_name()
            if not column_name:
                return

            # obliczenie mediany
            med = utils.get_median(self.data, column_name)

            # pokazanie mediany
            self.label_show_calculations.config(text=f"Median of {column_name} is {med}")

    def stdev(self):
        """
        Wybór kolumny do obliczenia odchylenia standardowego
        :return:
        """
        if isinstance(self.data, pd.DataFrame):
            # pobranie nazwy kolumny
            numerical_columns = utils.get_numerical_columns(self.data)
            if not numerical_columns:
                messagebox.showwarning("No numerical columns", "No numerical columns found in the data", parent=self)
                return
            dialog_window = DialogWindow(self, numerical_columns,
                                         "Select column to find standard deviation", "Select a numerical column")
            # pobranie nazwy kolumny
            column_name = dialog_window.get_column_name()
            if not column_name:
                return

            # obliczenie odchylenia standarowego
            stdev = utils.get_standard_deviation(self.data, column_name)

            # pokazanie odchylenia standardowego
            self.label_show_calculations.config(text=f"Standard deviation of {column_name} is {stdev}")

    def get_pca(self):
        """
        Wybór kolumny do analizy
        :return:
        """
        if not isinstance(self.data, pd.DataFrame):
            return
        # pobranie nazwy kolumny
        numerical_columns = utils.get_numerical_columns(self.data)
        if not numerical_columns:
            messagebox.showwarning("No numerical columns", "No numerical columns found in the data", parent=self)
            return
        dialog_window = AcceptPCAInputs(self, title="Enter PCA inputs", data=self.data,
                                        columns=self.data.columns.tolist())
        result = dialog_window.get_result()
        if not result:
            return

        target_column, n_components = result
        if not target_column or not n_components:
            return

        self.label_show_calculations.config(text=f"Calculating PCA for {target_column} with {n_components} components")

        # wyliczenie PCA
        pca = utils.get_pca(self.data, target_column, int(n_components))

        self.label_show_calculations.config(text=f"")

    def sammon(self):
        """
        :return:
        """
        if not isinstance(self.data, pd.DataFrame):
            return
        # pobranie nazwy kolumny
        numerical_columns = utils.get_numerical_columns(self.data)
        if not numerical_columns:
            messagebox.showwarning("No numerical columns", "No numerical columns found in the data", parent=self)
            return
        dialog_window = AcceptPCAInputs(self, title="Enter inputs for calculating Sammon", data=self.data,
                                        columns=self.data.columns.tolist())
        result = dialog_window.get_result()
        if not result:
            return

        target_column, n_components = result
        if not target_column or not n_components:
            return

        self.label_show_calculations.config(text=f"Calculating Sammon for {target_column} with {n_components}"
                                                 f" components")

        # obliczenie Sammona
        columns = self.data.columns.tolist()
        columns.remove(target_column)
        _data = self.data[columns]
        _names = self.data[target_column].unique().tolist()
        _target_data = self.data[target_column]
        data_matrix = _data.to_numpy()
        y, E = sammon.sammon(data_matrix, 2)  # zwraca 2 wymiarową macierz

        _plot_data = np.c_[y, _target_data]
        sammon.plot_sammon(_plot_data, names=_names, title="Sammon Mapping")

        self.label_show_calculations.config(text="")


if __name__ == '__main__':
    main_app = MainApplication()
    main_app.mainloop()
