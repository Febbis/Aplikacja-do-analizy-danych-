import os
import pandas as pd


def get_numerical_columns(df):
    """
    Zwraca liste nazw kolumn
    """
    return [col for col in df.columns if (df[col].dtype in ['int64', 'float64'])]


def get_average(df: pd.DataFrame, col: str):
    """
    Zwraca średnią kolumny
    """
    return df[col].mean()


def get_median(df: pd.DataFrame, col: str):
    """
    Zwraca medianę kolumny
    """
    return df[col].median()


def get_mode(df: pd.DataFrame, col: str):
    """
    Zwraca modę kolumny
    """
    return df[col].mode()[0]


def get_standard_deviation(df: pd.DataFrame, col: str):
    """
    Zwraca odchylenie standardowe kolumny
    """
    return df[col].std()


def get_pca(df: pd.DataFrame, target_col: str, n_components: int):
    """
    zwraca główną składową tabeli danych
    """
    from sklearn.decomposition import PCA
    __target_labels = df[target_col].unique()
    __target_labels.sort()
    __target_labels = __target_labels.tolist()

    _pca = PCA(n_components=n_components)
    _pca.fit(df.drop(target_col, axis=1))
    principal_components = _pca.transform(df.drop(target_col, axis=1))
    __column_names = [f"PC_{i}" for i in range(1, n_components + 1)]

    _principal_df = pd.DataFrame(principal_components, columns=__column_names)
    _principal_df[target_col] = df[target_col]

    # tworzenie wykresu dla główntch składowych
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(8, 8))
    sns.set(style="white")
    sns.set(font_scale=1.5)
    sns.set_color_codes("pastel")
    sns.scatterplot(x=__column_names[0], y=__column_names[1], hue=target_col, data=_principal_df)
    plt.show()


class Config:
    """
    Klasa przechowująca wartości konfiguracyjne
    """

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = {}
        self.load()

    def create_empty_file(self):
        with open(self.config_file, 'w') as f:
            f.write('# Configuration file for the project\n')

    def load(self):
        """
        ładowanie pliku konfiguracyjnego
        """
        if not os.path.exists(self.config_file):
            self.create_empty_file()
            return
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or line == '':  # komentarze, puste linie
                    continue
                key, value = line.split('=')
                self.config[key] = value

    def get(self, key: str):
        """
        Returns the value of a configuration key
        """
        return self.config.get(key) or ""

    def set(self, key: str, value: str):
        """
        Sets the value of a configuration key
        """
        self.config[key] = value

    def save(self):
        """
        zapis pliku konfiguracyjnego
        """
        with open(self.config_file, 'w') as f:
            for key, value in self.config.items():
                f.write(f'{key}={value}\n')
