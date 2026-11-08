"""English, Portuguese and Spanish UI catalogs and live Qt localization.

Portuguese source strings are stable lookup keys. Widget adapters retain the
original text so a language change never rewrites filenames, presets or IDs.
"""
from __future__ import annotations

import re
import string
from PySide6.QtCore import QObject, Signal, Qt, QCoreApplication, QTranslator
from PySide6.QtWidgets import (QLabel, QPushButton, QComboBox, QDialog,
                              QMessageBox, QInputDialog, QFileDialog)

LANGUAGES = {"en": "English", "pt": "Português", "es": "Español"}
DEFAULT_LANGUAGE = "en"

# Portuguese source | English | Spanish. Templates preserve interpolated data.
_ROWS = [
("Tema", "Theme", "Tema"),
("Tema do aplicativo", "Application theme", "Tema de la aplicación"),
("Idioma", "Language", "Idioma"),
("Idioma do aplicativo", "Application language", "Idioma de la aplicación"),
("Escuro", "Dark", "Oscuro"), ("Claro", "Light", "Claro"),
("Minimizar", "Minimize", "Minimizar"), ("Maximizar", "Maximize", "Maximizar"),
("Restaurar", "Restore", "Restaurar"), ("Fechar", "Close", "Cerrar"),
("Arraste seu vídeo para cá", "Drop your video here", "Arrastra tu vídeo aquí"),
("Ou clique para escolher o arquivo", "Or click to choose a file", "O haz clic para elegir un archivo"),
("Escolher vídeo", "Choose video", "Elegir vídeo"),
("Formatos: MP4, MOV, MKV, AVI, WEBM", "Formats: MP4, MOV, MKV, AVI, WEBM", "Formatos: MP4, MOV, MKV, AVI, WEBM"),
("Play / Pause (Espaço)", "Play / Pause (Space)", "Reproducir / Pausar (Espacio)"),
("Tela cheia", "Fullscreen", "Pantalla completa"),
("Tela cheia (sair: Esc ou duplo clique)", "Fullscreen (exit: Esc or double-click)", "Pantalla completa (salir: Esc o doble clic)"),
("Ver só o trecho marcado", "Preview selected range", "Ver solo el tramo marcado"),
("Marcar início", "Mark start", "Marcar inicio"), ("Marcar fim", "Mark end", "Marcar final"),
("Guardar este trecho", "Add clip", "Añadir recorte"),
("+ Tudo", "+ Full video", "+ Vídeo completo"),
("+ vídeo todo", "+ Full video", "+ Vídeo completo"),
("Adicionar o vídeo inteiro à lista de trechos", "Add the entire video to the clip list", "Añadir el vídeo completo a la lista de recortes"),
("Atalhos:  Espaço = play/pause  |  Q = início  |  E = fim  |  W / Enter = guardar  |  A / D = 1 segundo  |  Shift + A / D = quadro a quadro",
 "Shortcuts:  Space = play/pause  |  Q = start  |  E = end  |  W / Enter = add  |  A / D = 1 second  |  Shift + A / D = frame by frame",
 "Atajos:  Espacio = reproducir/pausar  |  Q = inicio  |  E = final  |  W / Enter = añadir  |  A / D = 1 segundo  |  Shift + A / D = fotograma a fotograma"),
("Seus trechos", "Your clips", "Tus recortes"),
("Seus trechos aparecerão aqui.\nMarque o começo e o fim no vídeo.", "Your clips will appear here.\nMark the start and end in the video.", "Tus recortes aparecerán aquí.\nMarca el inicio y el final en el vídeo."),
("Abrir outro vídeo...", "Open another video...", "Abrir otro vídeo..."),
("Remover trecho", "Remove clip", "Eliminar recorte"),
("Duração total de todos os recortes da lista", "Total duration of all clips in the list", "Duración total de todos los recortes de la lista"),
("Total: {0}", "Total: {0}", "Total: {0}"),
("Qualidade do vídeo", "Video quality", "Calidad del vídeo"),
("Original", "Original", "Original"),
("Sem perda · rápido", "Lossless · fast", "Sin pérdida · rápido"),
("WhatsApp leve", "WhatsApp compact", "WhatsApp ligero"),
("WhatsApp HD", "WhatsApp HD", "WhatsApp HD"),
("Personalizado", "Custom", "Personalizado"),
("Você escolhe tudo", "Choose your own settings", "Elige tus ajustes"),
("Salvar preset...", "Save preset...", "Guardar preset..."),
("Excluir preset", "Delete preset", "Eliminar preset"),
("Salvar preset", "Save preset", "Guardar preset"),
("Nome do preset:", "Preset name:", "Nombre del preset:"),
("Escolha um nome diferente dos presets padrão.", "Choose a name different from the built-in presets.", "Elige un nombre diferente de los presets predeterminados."),
('Substituir o preset "{0}"?', 'Replace preset "{0}"?', '¿Reemplazar el preset "{0}"?'),
('Excluir o preset "{0}"?', 'Delete preset "{0}"?', '¿Eliminar el preset "{0}"?'),
('Preset "{0}" salvo.', 'Preset "{0}" saved.', 'Preset "{0}" guardado.'),
('Preset "{0}" excluído.', 'Preset "{0}" deleted.', 'Preset "{0}" eliminado.'),
("TAMANHO DO VÍDEO", "VIDEO SIZE", "TAMAÑO DEL VÍDEO"),
("FLUIDEZ (FPS)", "FRAME RATE (FPS)", "FOTOGRAMAS (FPS)"),
("QUALIDADE", "QUALITY", "CALIDAD"),
("LIMITE DE TAMANHO", "FILE SIZE LIMIT", "LÍMITE DE TAMAÑO"),
("Máxima", "Maximum", "Máxima"), ("Alta", "High", "Alta"),
("Média", "Medium", "Media"), ("Baixa", "Low", "Baja"),
("Sem limite", "No limit", "Sin límite"),
("16 MB (WhatsApp)", "16 MB (WhatsApp)", "16 MB (WhatsApp)"),
("Acelerar com a placa de vídeo (NVIDIA)", "GPU acceleration (NVIDIA)", "Aceleración por GPU (NVIDIA)"),
("Placa NVIDIA não encontrada (usando o processador)", "NVIDIA GPU not found (using CPU)", "GPU NVIDIA no encontrada (usando CPU)"),
("Customizado…", "Custom…", "Personalizado…"),
("Customizado: {0}×{1}…", "Custom: {0}×{1}…", "Personalizado: {0}×{1}…"),
("Tamanho customizado", "Custom dimensions", "Dimensiones personalizadas"),
("Largura", "Width", "Anchura"), ("Altura", "Height", "Altura"),
("Aplicar", "Apply", "Aplicar"), ("Cancelar", "Cancel", "Cancelar"),
("A proporção do vídeo será preservada, com barras se necessário. Valores ímpares serão ajustados para o próximo número par.",
 "The video keeps its aspect ratio, with bars if needed. Odd values are rounded up to the next even number.",
 "Se conservará la proporción del vídeo, con barras si es necesario. Los valores impares se ajustarán al siguiente número par."),
("Resolução e FPS originais · Sem recompressão", "Original resolution and FPS · No re-encoding", "Resolución y FPS originales · Sin recodificación"),
("Resolução original", "Original resolution", "Resolución original"),
("FPS original", "Original FPS", "FPS originales"),
("Até {0}p", "Up to {0}p", "Hasta {0}p"),
("Até {0} fps", "Up to {0} fps", "Hasta {0} fps"),
("até {0} MB", "up to {0} MB", "hasta {0} MB"),
("qualidade {0}", "{0} quality", "calidad {0}"),
("Abra um vídeo para ver o resultado aqui.", "Open a video to see the output settings here.", "Abre un vídeo para ver aquí los ajustes de salida."),
("Mesma qualidade do original", "Same quality as the source", "Misma calidad que el original"),
(", sem recompressão.", ", without re-encoding.", ", sin recodificación."),
("{0}×{1} · {2} fps · ≈ {3} MB para {4} s", "{0}×{1} · {2} fps · ≈ {3} MB for {4} s", "{0}×{1} · {2} fps · ≈ {3} MB para {4} s"),
("O início do corte ajusta para o ponto mais próximo (a cada ~0,5 s) para não perder qualidade.",
 "The cut start snaps to a nearby keyframe to preserve quality.",
 "El inicio del recorte se ajusta a un fotograma clave cercano para conservar la calidad."),
("Vídeo com ≈ {0} Mbps para {1} s", "Video at ≈ {0} Mbps for {1} s", "Vídeo a ≈ {0} Mbps para {1} s"),
("Muito comprimido:", "Heavy compression:", "Compresión alta:"),
(" pode ficar borrado. Escolha um trecho menor ou um limite maior.", " the image may look blurry. Choose a shorter clip or a larger size limit.", " la imagen puede verse borrosa. Elige un recorte más corto o un límite mayor."),
("Pensado para o limite de 16 MB do envio normal.", "Configured for a 16 MB file size limit.", "Configurado para un límite de archivo de 16 MB."),
("Dica: no WhatsApp, envie como ", "Tip: on WhatsApp, send as a ", "Consejo: en WhatsApp, envía como "),
("Documento", "Document", "Documento"),
(" para ele não comprimir de novo.", " to avoid additional compression.", " para evitar otra compresión."),
("Usando a placa NVIDIA (rápido).", "Using NVIDIA GPU acceleration.", "Usando aceleración por GPU NVIDIA."),
("Usando o processador.", "Using the CPU.", "Usando la CPU."),
("Comece abrindo um vídeo: arraste o arquivo para a janela.", "Start by opening a video: drag the file into the window.", "Empieza abriendo un vídeo: arrastra el archivo a la ventana."),
("Passo 1:", "Step 1:", "Paso 1:"),
(" ache o começo do pedaço que você quer (clique na barra ou use A/D) e aperte ", " find the start of your clip (click the timeline or use A/D) and press ", " busca el inicio del recorte (haz clic en la barra o usa A/D) y pulsa "),
("Trecho guardado! Marque outro com ", "Clip added! Mark another with ", "¡Recorte añadido! Marca otro con "),
(" e ", " and ", " y "),
(", ou escolha a qualidade e salve à direita.", ", or choose the quality and export on the right.", ", o elige la calidad y exporta a la derecha."),
("Passo 2:", "Step 2:", "Paso 2:"),
(" agora ache o fim do pedaço e aperte ", " now find the end of your clip and press ", " ahora busca el final del recorte y pulsa "),
("Passo 3:", "Step 3:", "Paso 3:"),
(" aperte ", " press ", " pulsa "), (" ou ", " or ", " o "),
(" para guardar este trecho. Depois você pode marcar outros.", " to add this clip. You can then mark more clips.", " para añadir este recorte. Después puedes marcar otros."),
("Salvar", "Export", "Exportar"),
("Salvar cada trecho", "Export each clip", "Exportar cada recorte"),
("Juntar em um vídeo só", "Merge into one video", "Unir en un solo vídeo"),
("Só o áudio", "Audio only", "Solo audio"),
("WhatsApp (m4a leve)", "WhatsApp (compact M4A)", "WhatsApp (M4A ligero)"),
("Original (m4a sem perda)", "Original (lossless M4A)", "Original (M4A sin pérdida)"),
("WAV (sem compressão)", "WAV (uncompressed)", "WAV (sin compresión)"),
("Salvar em: mesma pasta do vídeo", "Save to: source video folder", "Guardar en: carpeta del vídeo"),
("Salvar em: {0}", "Save to: {0}", "Guardar en: {0}"),
("Mesma pasta do vídeo", "Source video folder", "Carpeta del vídeo"),
("Salvar em", "Save to", "Guardar en"),
("Pronto.", "Ready.", "Listo."), ("PROCESSAR", "PROCESS", "PROCESAR"),
("Abrir vídeo", "Open video", "Abrir vídeo"),
("Vídeos (*{0})", "Videos (*{0})", "Vídeos (*{0})"),
("Esse arquivo não parece ser um vídeo.", "This file does not appear to be a video.", "Este archivo no parece ser un vídeo."),
("Não consegui mostrar a prévia deste vídeo, mas você ainda pode marcar os tempos e salvar.", "The preview could not be loaded, but you can still mark times and export.", "No se pudo cargar la vista previa, pero aún puedes marcar los tiempos y exportar."),
("{0} - {1}  (analisando o vídeo...)", "{0} - {1}  (analyzing video...)", "{0} - {1}  (analizando vídeo...)"),
("{0} · {1} · pontos de corte a cada ~{2}s", "{0} · {1} · keyframes every ~{2}s", "{0} · {1} · fotogramas clave cada ~{2}s"),
("Trecho {0} guardado.", "Clip {0} added.", "Recorte {0} añadido."),
("Salvando os trechos...", "Exporting clips...", "Exportando recortes..."),
("Juntando os trechos...", "Merging clips...", "Uniendo recortes..."),
("Extraindo o áudio...", "Extracting audio...", "Extrayendo audio..."),
("{0} arquivo(s) salvo(s) em {1}", "{0} file(s) saved to {1}", "{0} archivo(s) guardado(s) en {1}"),
("{0} áudio(s) salvo(s) em {1}", "{0} audio file(s) saved to {1}", "{0} archivo(s) de audio guardado(s) en {1}"),
("Vídeo salvo (sem perda): {0}", "Video saved (lossless): {0}", "Vídeo guardado (sin pérdida): {0}"),
("Vídeo salvo (recodificado): {0}", "Video saved (re-encoded): {0}", "Vídeo guardado (recodificado): {0}"),
("Salvamento concluído", "Export complete", "Exportación completada"),
("Não foi possível salvar", "Export failed", "No se pudo exportar"),
("Abrir arquivo", "Open file", "Abrir archivo"),
("Abrir pasta", "Open folder", "Abrir carpeta"),
("Os trechos têm formatos diferentes (resolução, fps ou codec).\nPara juntar, o app precisa recodificar (alta qualidade, mais lento).\n\nContinuar?", "The clips have different formats (resolution, FPS or codec).\nMerging requires re-encoding (high quality, slower).\n\nContinue?", "Los recortes tienen formatos diferentes (resolución, FPS o códec).\nPara unirlos se requiere recodificar (alta calidad, más lento).\n\n¿Continuar?"),
("Cancelado.", "Canceled.", "Cancelado."),
("FFmpeg falhou:\n{0}", "FFmpeg failed:\n{0}", "FFmpeg falló:\n{0}"),
("Nao consegui ler o video:\n{0}", "Could not read the video:\n{0}", "No se pudo leer el vídeo:\n{0}"),
("O arquivo nao tem faixa de video.", "The file has no video stream.", "El archivo no tiene pista de vídeo."),
("Este video nao tem audio.", "This video has no audio.", "Este vídeo no tiene audio."),
("O fim do trecho precisa ser maior que o inicio.", "The clip end must be later than its start.", "El final del recorte debe ser posterior al inicio."),
("Nenhum trecho selecionado.", "No clips selected.", "No hay recortes seleccionados."),
("Não foi possível concluir a junção dos trechos.", "Could not finish merging clips.", "No se pudo completar la unión de los recortes."),
("FFmpeg nao encontrado. Rode: pip install imageio-ffmpeg (ou instale o FFmpeg e coloque no PATH).", "FFmpeg was not found. Run: pip install imageio-ffmpeg (or install FFmpeg and add it to PATH).", "No se encontró FFmpeg. Ejecuta: pip install imageio-ffmpeg (o instala FFmpeg y añádelo al PATH)."),
("Os trechos tem formatos diferentes (codec/resolucao/fps/audio), entao nao da para juntar sem recodificar.", "The clips have different formats (codec/resolution/FPS/audio) and cannot be merged without re-encoding.", "Los recortes tienen formatos diferentes (códec/resolución/FPS/audio) y no se pueden unir sin recodificar."),
]

CATALOGS = {language: {} for language in LANGUAGES}
for source, english, spanish in _ROWS:
    for language, translated in (("pt", source), ("en", english), ("es", spanish)):
        CATALOGS[language][source] = translated
# Native Qt strings use English keys, with explicit Portuguese translations.
_QT = {
    "Yes": ("Yes", "Sim", "Sí"), "No": ("No", "Não", "No"),
    "Cancel": ("Cancel", "Cancelar", "Cancelar"), "Close": ("Close", "Fechar", "Cerrar"),
    "OK": ("OK", "OK", "Aceptar"), "Open": ("Open", "Abrir", "Abrir"),
    "Save": ("Save", "Salvar", "Guardar"), "Apply": ("Apply", "Aplicar", "Aplicar"),
    "File name:": ("File name:", "Nome do arquivo:", "Nombre del archivo:"),
    "Files of type:": ("Files of type:", "Tipos de arquivo:", "Tipo de archivo:"),
    "Look in:": ("Look in:", "Examinar:", "Buscar en:"),
}
for source, translations in _QT.items():
    for language, value in zip(("en", "pt", "es"), translations):
        CATALOGS[language][source] = value

_LANGUAGE = DEFAULT_LANGUAGE
_FORMATTER = string.Formatter()
_TEMPLATES = []
_ALIASES = {}
for source in CATALOGS['pt']:
    variants = {language: catalog[source] for language, catalog in CATALOGS.items()}
    if '{' not in source:
        for text in variants.values():
            _ALIASES.setdefault(text, source)
    else:
        for pattern in set(variants.values()):
            regex = ''
            fields = []
            for literal, field, _, _ in _FORMATTER.parse(pattern):
                regex += re.escape(literal)
                if field is not None:
                    regex += '(.*?)'
                    fields.append(int(field))
            _TEMPLATES.append((re.compile('^' + regex + '$', re.DOTALL), fields, source))


def tr(text: str) -> str:
    """Translate UI text; template captures are preserved verbatim."""
    if not isinstance(text, str) or not text:
        return text
    source = _ALIASES.get(text)
    if source is not None:
        return CATALOGS[_LANGUAGE][source]
    stripped = text.strip()
    if stripped != text:
        translated = tr(stripped)
        if translated != stripped:
            start = len(text) - len(text.lstrip())
            return text[:start] + translated + text[len(text.rstrip()):]
    for regex, fields, source in _TEMPLATES:
        match = regex.fullmatch(text)
        if match:
            values = [''] * (max(fields, default=-1) + 1)
            for field, value in zip(fields, match.groups()):
                values[field] = value
            return CATALOGS[_LANGUAGE][source].format(*values)
    # Rich-text summaries preserve HTML and translate each visible text run.
    if '<' in text and '>' in text:
        return ''.join(part if part.startswith('<') else tr(part)
                       for part in re.split('(<[^>]+>)', text))
    if ' · ' in text:
        return ' · '.join(tr(part) for part in text.split(' · '))
    for operation in (str.upper, str.lower):
        for source in CATALOGS['pt']:
            if '{' not in source and operation(source) == text:
                return operation(CATALOGS[_LANGUAGE][source])
    return text


class _LanguageState(QObject):
    changed = Signal()


state = _LanguageState()
_QT_TRANSLATOR = None


class _QtTranslator(QTranslator):
    def isEmpty(self):
        return False

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        source = sourceText.replace('&', '')
        if source in _QT:
            return CATALOGS[_LANGUAGE][source]
        return ''


def set_language(language: str) -> str:
    global _LANGUAGE, _QT_TRANSLATOR
    language = language if language in LANGUAGES else DEFAULT_LANGUAGE
    _LANGUAGE = language
    app = QCoreApplication.instance()
    if app is not None and _QT_TRANSLATOR is None:
        _QT_TRANSLATOR = _QtTranslator(app)
        app.installTranslator(_QT_TRANSLATOR)
    state.changed.emit()
    return language


def get_language() -> str:
    return _LANGUAGE


class _TextWidget:
    """Keep raw UI text so switching language is reversible and immediate."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_text = self.text()
        self._source_tooltip = self.toolTip()
        self._source_accessible = self.accessibleName()
        state.changed.connect(self.retranslate)
        self.retranslate()

    def setText(self, text):
        self._source_text = text
        super().setText(tr(text))

    def setToolTip(self, text):
        self._source_tooltip = text
        super().setToolTip(tr(text))

    def setAccessibleName(self, text):
        self._source_accessible = text
        super().setAccessibleName(tr(text))

    def retranslate(self):
        # QLabel.setText clears its pixmap, even when the text is empty.
        pixmap = self.pixmap() if isinstance(self, QLabel) else None
        if pixmap is None or pixmap.isNull():
            super().setText(tr(self._source_text))
        super().setToolTip(tr(self._source_tooltip))
        super().setAccessibleName(tr(self._source_accessible))


class LocalizedLabel(_TextWidget, QLabel):
    pass


class LocalizedButton(_TextWidget, QPushButton):
    pass


_SOURCE_TEXT_ROLE = int(Qt.UserRole) + 100
_SOURCE_DATA_ROLE = int(Qt.UserRole) + 101
_RAW_ROLE = int(Qt.UserRole) + 102


class LocalizedComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_tooltip = ''
        self._source_accessible = ''
        state.changed.connect(self.retranslate)

    def addItem(self, text, userData=None, *, localize=True):
        super().addItem(tr(text) if localize else text, userData)
        row = self.count() - 1
        super().setItemData(row, text, _SOURCE_TEXT_ROLE)
        super().setItemData(row, not localize, _RAW_ROLE)

    def setItemText(self, index, text):
        super().setItemData(index, text, _SOURCE_TEXT_ROLE)
        super().setItemText(index, text if self.itemData(index, _RAW_ROLE) else tr(text))

    def setItemData(self, index, value, role=Qt.UserRole):
        if role in (Qt.ToolTipRole, Qt.AccessibleDescriptionRole, int(Qt.UserRole) + 1) and isinstance(value, str):
            values = self.itemData(index, _SOURCE_DATA_ROLE) or {}
            values[int(role)] = value
            super().setItemData(index, values, _SOURCE_DATA_ROLE)
            super().setItemData(index, tr(value), role)
        else:
            super().setItemData(index, value, role)

    def setToolTip(self, text):
        self._source_tooltip = text
        super().setToolTip(tr(text))

    def setAccessibleName(self, text):
        self._source_accessible = text
        super().setAccessibleName(tr(text))

    def retranslate(self):
        previous = self.blockSignals(True)
        try:
            for row in range(self.count()):
                source = self.itemData(row, _SOURCE_TEXT_ROLE)
                if source is not None and not self.itemData(row, _RAW_ROLE):
                    super().setItemText(row, tr(source))
                for role, value in (self.itemData(row, _SOURCE_DATA_ROLE) or {}).items():
                    super().setItemData(row, tr(value), int(role))
            super().setToolTip(tr(self._source_tooltip))
            super().setAccessibleName(tr(self._source_accessible))
        finally:
            self.blockSignals(previous)


class LocalizedDialog(QDialog):
    def setWindowTitle(self, title):
        super().setWindowTitle(tr(title))


class LocalizedMessageBox(QMessageBox):
    def setText(self, text):
        super().setText(tr(text))

    def setInformativeText(self, text):
        super().setInformativeText(tr(text))

    def addButton(self, *args):
        if args and isinstance(args[0], str):
            args = (tr(args[0]), *args[1:])
        return super().addButton(*args)

    @staticmethod
    def warning(parent, title, text, *args):
        return QMessageBox.warning(parent, tr(title), tr(text), *args)

    @staticmethod
    def question(parent, title, text, *args):
        return QMessageBox.question(parent, tr(title), tr(text), *args)


class LocalizedInputDialog(QInputDialog):
    @staticmethod
    def getText(parent, title, label, *args, **kwargs):
        return QInputDialog.getText(parent, tr(title), tr(label), *args, **kwargs)


class LocalizedFileDialog(QFileDialog):
    @staticmethod
    def getOpenFileNames(parent, caption='', directory='', filter='', *args, **kwargs):
        return QFileDialog.getOpenFileNames(parent, tr(caption), directory, tr(filter), *args, **kwargs)

    @staticmethod
    def getExistingDirectory(parent, caption='', directory='', *args, **kwargs):
        return QFileDialog.getExistingDirectory(parent, tr(caption), directory, *args, **kwargs)
