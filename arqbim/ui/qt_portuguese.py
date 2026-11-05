"""(0.330) Qt's own words in the Portuguese of Portugal: the standard buttons (OK, Cancelar, Guardar, Não guardar, Sim,
Não…), the window to save and open files (Guardar como, Nome do ficheiro, Pasta acima, Eliminar…), the colour window,
the menus of the text boxes (Desfazer, Cortar, Colar…), the panels' and tabs' own buttons. Qt brings only the
Portuguese of Brazil (qtbase_pt_BR: «Salvar», «Arquivo», «Excluir», «Exibição», «tela», «aba»); it is kept
underneath, for a text not listed here, and this translator, installed over it, answers first. A text listed as
None stays as Qt has it (Qt reads keys such as Alt+Left back from their text: translated, they would stop working).

WORDS: {context: {Qt's English text: ours}} — what a probe found Qt asking for in the windows the program shows, and
the texts Qt says only on the way (a file that exists already, one deleted)."""

from PySide6 import QtCore

_KEEP = None

WORDS = {
    "QPlatformTheme": {                 # (the standard buttons of every window: QMessageBox, QDialogButtonBox)
        "OK": "OK", "Save": "Guardar", "Save All": "Guardar tudo", "Open": "Abrir", "&Yes": "&Sim",
        "Yes to &All": "Sim para &todos", "&No": "&Não", "N&o to All": "Nã&o para todos", "Abort": "Interromper",
        "Retry": "Tentar de novo", "Ignore": "Ignorar", "Close": "Fechar", "Cancel": "Cancelar",
        "Discard": "Não guardar", "Don't Save": "Não guardar", "Close without Saving": "Fechar sem guardar",
        "Help": "Ajuda", "Apply": "Aplicar", "Reset": "Repor", "Restore Defaults": "Repor predefinições",
    },
    "QMessageBox": {
        "Show Details...": "Mostrar detalhes…", "Hide Details...": "Ocultar detalhes…", "OK": "OK",
    },
    "QProgressDialog": {"Cancel": "Cancelar"},
    "QInputDialog": {"Enter a value:": "Introduza um valor:"},
    "QFileDialog": {
        "&Look in:": "&Procurar em:", "File &name:": "&Nome do ficheiro:", "Files of &type:": "Ficheiros do &tipo:",
        "Directory:": "Pasta:", "&Save": "&Guardar", "&Open": "&Abrir", "&Choose": "Es&colher",
        "Save As": "Guardar como", "Open": "Abrir", "Find Directory": "Procurar pasta",
        "&Delete": "&Eliminar", "&Rename": "&Mudar o nome", "&New Folder": "&Nova pasta", "New Folder": "Nova pasta",
        "Show &hidden files": "Mostrar ficheiros &ocultos", "All Files (*)": "Todos os ficheiros (*)",
        "Directories": "Pastas", "Files": "Ficheiros", "Back": "Retroceder", "Forward": "Avançar",
        "Parent Directory": "Pasta acima", "Create New Folder": "Criar nova pasta", "List View": "Vista de lista",
        "Detail View": "Vista de detalhes", "Go back": "Retroceder", "Go forward": "Avançar",
        "Go to the parent directory": "Ir para a pasta acima", "Create a New Folder": "Cria uma nova pasta",
        "Change to list view mode": "Mostrar em lista", "Change to detail view mode": "Mostrar com detalhes",
        "List of places and bookmarks": "Lista de locais e marcadores", "Sidebar": "Barra lateral",
        "Show ": "Mostrar ", "Recent Places": "Locais recentes", "My Computer": "O meu computador",
        "Alt+Left": _KEEP, "Alt+Right": _KEEP, "Alt+Up": _KEEP,
        "%1 already exists.\nDo you want to replace it?": "%1 já existe.\nQuer substituí-lo?",
        "%1\nFile not found.\nPlease verify the correct file name was given.":
            "%1\nO ficheiro não foi encontrado.\nVerifique se o nome está certo.",
        "%1\nDirectory not found.\nPlease verify the correct directory name was given.":
            "%1\nA pasta não foi encontrada.\nVerifique se o nome está certo.",
        "Are you sure you want to delete '%1'?": "Quer mesmo eliminar «%1»?",
        "'%1' is write protected.\nDo you want to delete it anyway?":
            "«%1» está protegido contra escrita.\nQuer eliminá-lo mesmo assim?",
        "Could not delete directory.": "Não foi possível eliminar a pasta.",
    },
    "QFileSystemModel": {
        "Name": "Nome", "Size": "Tamanho", "Type": "Tipo", "Kind": "Tipo", "Date Modified": "Data de modificação",
        "Computer": "Computador", "My Computer": "O meu computador", "Invalid filename": "Nome de ficheiro inválido",
        "<b>The name \"%1\" cannot be used.</b><p>Try using another name, with fewer characters or no punctuation "
        "marks.": "<b>O nome «%1» não pode ser usado.</b><p>Experimente outro nome, mais curto ou sem pontuação.",
    },
    "QAbstractFileIconProvider": {
        "Folder": "Pasta", "File": "Ficheiro", "%1 File": "Ficheiro %1", "Drive": "Unidade", "Shortcut": "Atalho",
        "Alias": "Atalho", "Unknown": "Desconhecido",
    },
    "QColorDialog": {
        "Select Color": "Escolher cor", "&Basic colors": "Cores &básicas", "&Custom colors": "Cores &personalizadas",
        "&Add to Custom Colors": "&Juntar às cores personalizadas", "&Pick Screen Color": "&Tirar cor do ecrã",
        "Hu&e:": "Ma&tiz:", "&Sat:": "&Sat:", "&Val:": "&Val:", "&Red:": "&Vermelho:", "&Green:": "V&erde:",
        "Bl&ue:": "Az&ul:", "A&lpha channel:": "Canal a&lfa:", "&HTML:": "&HTML:",
        "Cursor at %1, %2\nPress ESC to cancel": "Cursor em %1, %2\nPrima Esc para cancelar",
    },
    "QLineEdit": {
        "&Undo": "&Desfazer", "&Redo": "&Refazer", "Cu&t": "Cor&tar", "&Copy": "&Copiar", "&Paste": "C&olar",
        "Delete": "Eliminar", "Select All": "Selecionar tudo",
    },
    "QWidgetTextControl": {
        "&Undo": "&Desfazer", "&Redo": "&Refazer", "Cu&t": "Cor&tar", "&Copy": "&Copiar", "&Paste": "C&olar",
        "Delete": "Eliminar", "Select All": "Selecionar tudo", "Copy &Link Location": "Copiar o endereço da &ligação",
    },
    "QAbstractSpinBox": {"&Select All": "&Selecionar tudo", "&Step up": "&Aumentar", "Step &down": "&Diminuir"},
    "QDockWidget": {
        "Close": "Fechar", "Closes the dock widget": "Fecha o painel", "Float": "Destacar",
        "Undocks and re-attaches the dock widget": "Solta o painel da janela e volta a prendê-lo",
    },
    "CloseButton": {"Close Tab": "Fechar separador"},
    "QTabBar": {"Scroll Left": "Deslocar para a esquerda", "Scroll Right": "Deslocar para a direita"},
}
# the keys' names (Ctrl, Shift, Delete, Space…) as the program has always shown them, and its texts name them
KEPT = ("QShortcut",)


class PortugueseQt(QtCore.QTranslator):
    """The words of WORDS; the texts of KEPT as they are; None for the others — Qt then asks the translator
    underneath, and keeps its own text when none knows it. (Not "": Qt takes any text that is not null, an empty one
    too, as the translation — every text not listed came out blank, the calculation report's PDF too.)"""

    def translate(self, context, source, disambiguation=None, n=-1):
        if context in KEPT:
            return source
        words = WORDS.get(context)
        if words is None or source not in words:
            return None
        text = words[source]
        return source if text is _KEEP else text

    def isEmpty(self):
        return False


_installed = []          # (kept here: Qt does not own the translators it is given)


def install(app):
    """Qt's words in Portuguese of Portugal, once: Qt's Brazilian translation underneath (when it is there), ours over
    it. Returns the translators installed."""
    if _installed:
        return list(_installed)
    folder = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
    brazil = QtCore.QTranslator(app)
    if brazil.load("qtbase_pt_BR", folder):
        app.installTranslator(brazil)
        _installed.append(brazil)
    ours = PortugueseQt(app)
    app.installTranslator(ours)
    _installed.append(ours)
    return list(_installed)
