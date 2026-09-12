# -*- coding: utf-8 -*-
"""
Día 10 - Mi Tablero (Comunicación Aumentativa · CAA)  ·  PySide6
----------------------------------------------------------------
Le da voz a personas que no pueden hablar (autismo no verbal, ictus, parálisis...).
Se toca una serie de pictogramas para armar una frase y la computadora la DICE en voz alta.

  · Rejilla de botones por categorías (con color, convención CAA).
  · Barra de frase + Hablar / Borrar / Vaciar.
  · Voz en español con QTextToSpeech (offline). Si el sistema no tiene voz en
    español, usa la disponible y avisa cómo instalar una.
  · Modo edición para añadir botones propios (palabra + emoji). Se guarda solo.

Todo local, sin internet. Ejecuta con "Tablero.bat".
Autor: KALEVI LATVA AIJO ALEGRIA
"""

import sys
import os
import json
import wave
import tempfile
import hashlib
import threading

try:
    import winsound   # reproducir WAV en Windows (stdlib, sin dependencias)
except ImportError:
    winsound = None

# En modo pythonw (sin consola) sys.stdout/stderr son None; algunas librerías (tqdm, transformers)
# fallan al imprimir mientras cargan la voz -> se redirige a un "sumidero" para que no crashee.
if sys.stdout is None or sys.stderr is None:
    _dev = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = _dev
    if sys.stderr is None:
        sys.stderr = _dev

from PySide6.QtCore import Qt, Signal, QObject, QTimer, QLocale, QSettings
from PySide6.QtGui import QFont
from PySide6.QtTextToSpeech import QTextToSpeech
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QCheckBox, QFrame, QScrollArea,
    QHBoxLayout, QVBoxLayout, QGridLayout, QDialog, QLineEdit, QSizePolicy,
    QPlainTextEdit, QFileDialog, QMessageBox,
)

# ------------------------------------------------------------ vocabulario (desde vocabulario.json)
def _cargar_vocabulario():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocabulario.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)   # {cat: [nombre, color, [[emoji, palabra], ...]]}
    except Exception:
        return {"frecuentes": ["Frecuentes", "#fde68a",
                [["🙋", "yo"], ["👉", "tú"], ["❤️", "quiero"], ["👍", "sí"], ["👎", "no"], ["🆘", "ayuda"]]]}

BASE = _cargar_vocabulario()
EMOJIS = ["⭐", "😀", "😢", "😠", "😴", "🤕", "😨", "🥰", "😋", "🙂", "🙁", "👍", "👎", "🙏", "🤟", "👋", "✋", "🤗", "👀", "👂", "🙋", "👉",
          "💧", "🍽️", "🍞", "🥛", "🍎", "🍌", "🍚", "🍪", "🍫", "🧃", "🍕", "🍔", "🥤", "🍇", "🥕",
          "🎮", "📖", "🎵", "⚽", "🚗", "🚽", "🛁", "🚪", "🚶", "🛌", "✏️", "🎨", "📺",
          "🏠", "🏫", "🏥", "🏪", "🌳", "🛏️", "🍳", "🛋️", "🌙", "☀️", "⏰",
          "👩", "👨", "👵", "👴", "👶", "🧒", "👪", "👨‍⚕️", "👩‍🏫", "🐶", "🐱",
          "❤️", "➕", "🔚", "🆘", "✅", "❌", "❓", "🔁", "💊", "🩹", "😷"]

EMOJI_FONT = "Segoe UI Emoji"


# ------------------------------------------------------------ tile
class Tile(QFrame):
    clicked = Signal()
    eliminar = Signal()

    def __init__(self, emo, txt, bg):
        super().__init__()
        self.setObjectName("tile")
        self.setStyleSheet(f"#tile {{ background:{bg}; border:3px solid rgba(0,0,0,0.08); border-radius:18px; }}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignmentFlag.AlignCenter); v.setSpacing(2)
        e = QLabel(emo); e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        e.setFont(QFont(EMOJI_FONT, 28)); e.setStyleSheet("background:transparent; border:none;")
        t = QLabel(txt); t.setAlignment(Qt.AlignmentFlag.AlignCenter); t.setWordWrap(True)
        t.setStyleSheet("background:transparent; border:none; font-weight:700; font-size:14px; color:#1f2937;")
        v.addWidget(e); v.addWidget(t)
        self.del_btn = QPushButton("✕", self); self.del_btn.setObjectName("del")
        self.del_btn.setFixedSize(26, 26); self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.clicked.connect(lambda: self.eliminar.emit()); self.del_btn.hide()

    def resizeEvent(self, e):
        self.del_btn.move(self.width() - 30, 4)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def set_edit(self, on):
        self.del_btn.setVisible(on)


# ------------------------------------------------------------ diálogo añadir
class DialogoAnadir(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir botón")
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self.emoji = "⭐"
        self.resize(440, 420)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("<b>Palabra o frase</b>"))
        self.word = QLineEdit(); self.word.setPlaceholderText("Ej: quiero jugar"); self.word.setMaxLength(24)
        v.addWidget(self.word)
        v.addWidget(QLabel("<b>Elige un dibujo</b>"))
        area = QScrollArea(); area.setWidgetResizable(True); area.setFixedHeight(200)
        host = QWidget(); g = QGridLayout(host); g.setSpacing(4)
        self.botones = []
        for i, em in enumerate(EMOJIS):
            b = QPushButton(em); b.setFont(QFont(EMOJI_FONT, 20)); b.setFixedSize(46, 46)
            b.setCheckable(True); b.setObjectName("emo")
            b.clicked.connect(lambda _=False, e=em, bt=b: self._pick(e, bt))
            g.addWidget(b, i // 7, i % 7); self.botones.append(b)
        self.botones[0].setChecked(True)
        area.setWidget(host); v.addWidget(area)
        row = QHBoxLayout()
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        ok = QPushButton("Añadir"); ok.setObjectName("primary"); ok.clicked.connect(self.accept)
        row.addWidget(cancel); row.addWidget(ok); v.addLayout(row)

    def _pick(self, em, bt):
        self.emoji = em
        for b in self.botones:
            b.setChecked(b is bt)


# ------------------------------------------------------------ cambiar la voz (grabar / cargar)
GUION_VOZ = (
    "Lee esto con calma, en un lugar silencioso y a volumen normal:\n\n"
    "Hola, esta es una grabación tranquila y clara de mi voz.\n"
    "El veloz murciélago hindú comía feliz cardillo y kiwi.\n"
    "El perro de Rodrigo corre por el barro; el carro arranca y frena.\n"
    "La niña pequeña llevaba un chal amarillo y jugaba en el jardín.\n"
    "Hoy hace buen día: quiero pausar, reunir seis ideas nuevas y continuar.\n"
    "¿Cuánto cuesta esto? Uno, dos, tres, cuatro, cinco. Muchas gracias."
)


class _Grabadora:
    """Graba del micrófono (inicio/fin) con sounddevice."""
    def __init__(self, sr=44100):
        self.sr = sr
        self.frames = []
        self.stream = None

    def start(self):
        import sounddevice as sd
        self.frames = []
        self.stream = sd.InputStream(samplerate=self.sr, channels=1, callback=self._cb)
        self.stream.start()

    def _cb(self, indata, frames, time_info, status):
        self.frames.append(indata.copy())

    def stop(self):
        import numpy as np
        if self.stream:
            self.stream.stop(); self.stream.close(); self.stream = None
        if self.frames:
            return np.concatenate(self.frames, axis=0).flatten(), self.sr
        return None, self.sr


def _procesar_referencia(audio, sr_in):
    """Deja una referencia limpia (mono, mejor tramo ~16s, normalizada, 24kHz). Sin reductor de ruido."""
    import numpy as np, soundfile as sf, torch, torchaudio, tempfile
    data = np.asarray(audio, dtype=np.float32)
    win = int(16 * sr_in)
    if len(data) > win:
        thr = np.max(np.abs(data)) * 0.06
        voiced = (np.abs(data) > thr).astype(np.float32)
        cs = np.cumsum(voiced)
        best_i, best = 0, -1.0
        for i in range(0, len(data) - win, int(0.25 * sr_in)):
            s = cs[i + win] - cs[i]
            if s > best:
                best, best_i = s, i
        data = data[best_i:best_i + win]
    idx = np.where(np.abs(data) > np.max(np.abs(data)) * 0.04)[0]
    if len(idx):
        pad = int(0.05 * sr_in)
        data = data[max(0, idx[0] - pad):min(len(data), idx[-1] + pad)]
    peak = float(np.max(np.abs(data))) or 1.0
    data = data * (0.97 / peak)
    t = torchaudio.functional.resample(torch.from_numpy(data).unsqueeze(0), sr_in, 24000)
    out = os.path.join(tempfile.gettempdir(), "caa_ref_nueva.wav")
    sf.write(out, t.squeeze(0).numpy(), 24000, subtype="PCM_16")
    return out


class DialogoVoz(QDialog):
    """Cambiar la voz del tablero: grabar una voz de confianza o cargar un archivo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar la voz")
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self.resize(560, 600)
        self.ref_final = None
        self._grab = None
        self._elapsed = 0.0

        v = QVBoxLayout(self)
        v.addWidget(QLabel("<b>¿De quién es esta voz?</b>  (ej. Mamá, Papá, Ana)"))
        self.nombre = QLineEdit(); self.nombre.setPlaceholderText("Mi voz"); v.addWidget(self.nombre)

        v.addWidget(QLabel("<b>Forma 1 · Grabar</b> — que la persona lea esto con calma:"))
        g = QPlainTextEdit(GUION_VOZ); g.setReadOnly(True); g.setFixedHeight(150); v.addWidget(g)
        r1 = QHBoxLayout()
        self.btn_rec = QPushButton("🎤  Grabar"); self.btn_rec.clicked.connect(self._toggle_rec)
        self.lbl_time = QLabel("")
        r1.addWidget(self.btn_rec); r1.addWidget(self.lbl_time); r1.addStretch(); v.addLayout(r1)

        v.addWidget(QLabel("<b>Forma 2 · Cargar un archivo de audio</b>"))
        self.btn_file = QPushButton("📁  Elegir archivo (.wav .mp3 …)"); self.btn_file.clicked.connect(self._elegir)
        v.addWidget(self.btn_file)

        self.estado = QLabel(""); self.estado.setWordWrap(True); v.addWidget(self.estado)

        self.volver_default = False
        self.btn_reset = QPushButton("↩  Volver a mi voz original")
        self.btn_reset.clicked.connect(lambda: (setattr(self, "volver_default", True), self.accept()))
        v.addWidget(self.btn_reset)

        r2 = QHBoxLayout()
        self.btn_prev = QPushButton("▶  Escuchar"); self.btn_prev.clicked.connect(self._preview); self.btn_prev.setEnabled(False)
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("✓  Usar esta voz"); self.btn_ok.setObjectName("primary")
        self.btn_ok.clicked.connect(self.accept); self.btn_ok.setEnabled(False)
        r2.addWidget(self.btn_prev); r2.addStretch(); r2.addWidget(cancel); r2.addWidget(self.btn_ok); v.addLayout(r2)

        self._timer = QTimer(self); self._timer.timeout.connect(self._tick)

    def _toggle_rec(self):
        if self._grab is None:
            try:
                self._grab = _Grabadora()
                self._grab.start()
            except Exception as e:
                self.estado.setText(f"No pude usar el micrófono: {e}"); self._grab = None; return
            self._elapsed = 0.0; self._timer.start(500)
            self.btn_rec.setText("⏹  Detener"); self.estado.setText("● Grabando… lee el texto con calma.")
        else:
            self._timer.stop()
            audio, sr = self._grab.stop(); self._grab = None
            self.btn_rec.setText("🎤  Grabar de nuevo")
            if audio is not None and len(audio) > sr * 3:
                self._preparar(audio, sr)
            else:
                self.estado.setText("La grabación es muy corta; intenta de nuevo (10-30 s).")

    def _tick(self):
        self._elapsed += 0.5; self.lbl_time.setText(f"{self._elapsed:.0f} s")

    def _elegir(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir audio", "", "Audio (*.wav *.mp3 *.flac *.ogg *.m4a)")
        if not ruta:
            return
        try:
            import soundfile as sf, numpy as np
            data, sr = sf.read(ruta)
            if data.ndim > 1:
                data = data.mean(axis=1)
            self._preparar(np.asarray(data, dtype="float32"), sr)
        except Exception as e:
            self.estado.setText(f"No pude leer el archivo: {e}")

    def _preparar(self, audio, sr):
        self.estado.setText("Procesando la voz…")
        try:
            self.ref_final = _procesar_referencia(audio, sr)
            self.btn_prev.setEnabled(True); self.btn_ok.setEnabled(True)
            self.estado.setText("✓  Voz lista. Pulsa «Escuchar» para probarla y «Usar esta voz» para aplicarla.")
        except Exception as e:
            self.estado.setText(f"Error procesando: {e}")

    def _preview(self):
        if self.ref_final and winsound:
            try:
                winsound.PlaySound(self.ref_final, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass


# ------------------------------------------------------------ voz en vivo (Chatterbox)
class VozViva(QObject):
    """Genera TU voz en vivo para cualquier texto (frase o palabra) y la reproduce.
    Solo funciona en el entorno con GPU (Chatterbox). Cachea por texto -> repetir es instantáneo.
    """
    listo = Signal(bool)          # modelo cargado (True) o falló (False)
    estado = Signal(str)          # "hablando" / "listo"
    palabra_lista = Signal(str, str)   # (palabra, ruta_wav) tras empaquetarla en tu voz

    def __init__(self, ref, cache_dir, parent=None):
        super().__init__(parent)
        self.ref = ref
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.model = None
        self.wmodel = None        # Whisper (para empaquetar palabras sueltas limpias)
        self.sr = 24000
        self._lock = threading.Lock()

    def cargar_async(self):
        threading.Thread(target=self._cargar, daemon=True).start()

    def _cargar(self):
        try:
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = ChatterboxMultilingualTTS.from_pretrained(device=dev)
            self.sr = self.model.sr
            try:
                import whisper
                self.wmodel = whisper.load_model("small", device=dev)
            except Exception:
                self.wmodel = None
            self.listo.emit(True)
        except Exception:
            self.model = None
            self.listo.emit(False)

    @property
    def puede_empaquetar(self):
        return self.model is not None and self.wmodel is not None

    def set_referencia(self, path):
        """Cambia la voz de referencia. Borra el caché de frases (eran de la voz anterior)."""
        self.ref = path
        try:
            import glob
            for f in glob.glob(os.path.join(self.cache_dir, "*.wav")):
                os.remove(f)
        except Exception:
            pass

    def empaquetar_async(self, palabra, out_path):
        """Genera la palabra en TU voz (robusto) y la guarda permanente en out_path."""
        threading.Thread(target=self._empaquetar, args=(palabra, out_path), daemon=True).start()

    def _empaquetar(self, palabra, out_path):
        try:
            import numpy as np
            import soundfile as sf
            import build_voz as bv
            with self._lock:
                arr, _modo = bv.generar_palabra(self.model, self.wmodel, palabra, self.sr)
            if arr is None:
                self.palabra_lista.emit(palabra, "")
                return
            sf.write(out_path, arr, self.sr, subtype="PCM_16")
            self.palabra_lista.emit(palabra, out_path)
        except Exception:
            self.palabra_lista.emit(palabra, "")

    @property
    def ready(self):
        return self.model is not None

    def _path(self, text):
        h = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, h + ".wav")

    def _play(self, p):
        if winsound and p and os.path.exists(p):
            try:
                winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    def hablar(self, text):
        text = (text or "").strip()
        if not text or not self.ready:
            return False
        p = self._path(text)
        if os.path.exists(p):          # ya generado -> instantáneo
            self._play(p)
            return True
        self.estado.emit("hablando")
        threading.Thread(target=self._gen_play, args=(text, p), daemon=True).start()
        return True

    def _gen_play(self, text, p):
        try:
            import numpy as np
            import soundfile as sf
            with self._lock:
                wav = self.model.generate(text, language_id="es", audio_prompt_path=self.ref,
                                          exaggeration=0.5, cfg_weight=0.5, temperature=0.6)
            arr = (wav.cpu() if wav.is_cuda else wav).squeeze().numpy().astype(np.float32)
            # recortar silencio de extremos + fade + normalizar (frases: sin whisper, salen limpias)
            thr = max(0.015, float(np.max(np.abs(arr))) * 0.05)
            idx = np.where(np.abs(arr) > thr)[0]
            if len(idx):
                arr = arr[max(0, idx[0] - int(0.02 * self.sr)):min(len(arr), idx[-1] + int(0.04 * self.sr))]
            f = int(self.sr * 0.015)
            if len(arr) > 2 * f:
                r = np.linspace(0, 1, f, dtype=np.float32); arr[:f] *= r; arr[-f:] *= r[::-1]
            arr = arr * (0.95 / (float(np.max(np.abs(arr))) or 1.0))
            sf.write(p, arr, self.sr, subtype="PCM_16")
            self._play(p)
        except Exception:
            pass
        finally:
            self.estado.emit("listo")


# ------------------------------------------------------------ ventana
class Tablero(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi Tablero — Comunicación")
        self.resize(1060, 760)
        self.setStyleSheet(ESTILO)

        self.settings = QSettings("KaleviApps", "TableroCAA")
        self.board = self._cargar_board()
        self.cat = "frecuentes"
        self.sentence = []
        self.editing = False
        self.say_on_tap = self.settings.value("sayOnTap", True, type=bool)

        self._setup_tts()
        self._cargar_voz_cache()
        self.voz_viva = None
        self.voz_viva_ok = False
        self._ui()
        self._render_cats()
        self._render_grid()
        self._iniciar_voz_viva()

    def _iniciar_voz_viva(self):
        """Arranca la voz en vivo (Chatterbox) si el entorno la tiene. Dice CUALQUIER texto."""
        base = os.path.dirname(os.path.abspath(__file__))
        ref = os.path.join(base, "voz_referencia.wav")
        self.custom_voz = False
        self.voz_nombre = self.settings.value("voz_ref_nombre", "", type=str)
        custom = self.settings.value("voz_ref_path", "", type=str)
        if custom and os.path.exists(custom):
            ref = custom; self.custom_voz = True; self.voz_cache = {}   # voz elegida -> todo en vivo
        if not os.path.exists(ref):
            return
        self.voz_viva = VozViva(ref, os.path.join(base, "voz_cache_live"), self)
        self.voz_viva.listo.connect(self._voz_viva_lista)
        self.voz_viva.estado.connect(self._voz_estado)
        self.voz_viva.palabra_lista.connect(self._palabra_empaquetada)
        self._set_voz_banner("⏳  Cargando tu voz… en un momento podrás decir cualquier cosa.")
        self.voz_viva.cargar_async()

    def _guardar_manifest(self):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voz_cache")
        try:
            palabras = {w: os.path.basename(p) for w, p in self.voz_cache.items()}
            with open(os.path.join(base, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump({"sr": self.voz_sr, "words": palabras}, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _empaquetar_palabra(self, w):
        """Genera 'w' en tu voz y la guarda permanente (si hay motor en vivo con GPU)."""
        if not w or w in self.voz_cache:
            return
        if self.voz_viva and self.voz_viva.puede_empaquetar:
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voz_cache")
            os.makedirs(base, exist_ok=True)
            fn = "new_" + hashlib.md5(w.encode("utf-8")).hexdigest()[:12] + ".wav"
            self._set_voz_banner(f"⏳  Generando «{w}» en tu voz…")
            self.voz_viva.empaquetar_async(w, os.path.join(base, fn))

    def _palabra_empaquetada(self, palabra, ruta):
        if ruta and os.path.exists(ruta):
            self.voz_cache[palabra] = ruta
            self._guardar_manifest()
            self._set_voz_banner(f"🎙️  «{palabra}» añadida en tu voz ✓  ·  {len(self.voz_cache)} palabras")
            self._play_wav(ruta)      # dar feedback: decir la palabra recién creada
        else:
            self._set_voz_banner(f"No pude generar «{palabra}» en tu voz; usará la del sistema.")

    def _voz_viva_lista(self, ok):
        self.voz_viva_ok = ok
        if ok:
            quien = f"de «{self.voz_nombre}»" if self.custom_voz and self.voz_nombre else "lista"
            self._set_voz_banner(f"🎙️  Tu voz {quien} — di cualquier palabra o frase (se genera al instante).")
        elif self.voz_cache:
            # Sin GPU (p.ej. .exe): solo las palabras pre-generadas en tu voz.
            self._set_voz_banner(f"🎙️  Tu voz · {len(self.voz_cache)} palabras (sin GPU aquí: solo estas).")

    def _abrir_dialogo_voz(self):
        """Cambiar la voz del tablero: grabar una voz de confianza o cargar un archivo."""
        if self.voz_viva is None:
            QMessageBox.information(self, "Cambiar la voz",
                                   "Esta versión no tiene el motor de voz (necesita GPU).\n"
                                   "Ábrelo con «Tablero-mi-voz.bat» para grabar o cargar una voz.")
            return
        if not self.voz_viva_ok:
            QMessageBox.information(self, "Cambiar la voz",
                                   "La voz todavía se está cargando.\n"
                                   "Espera a que arriba diga «🎙️ Tu voz lista» e inténtalo otra vez.")
            return
        d = DialogoVoz(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            if getattr(d, "volver_default", False):
                self._aplicar_voz_default()
            elif d.ref_final:
                import shutil
                base = os.path.dirname(os.path.abspath(__file__))
                nombre = d.nombre.text().strip() or "voz elegida"
                dst = os.path.join(base, "voz_referencia_custom.wav")
                try:
                    shutil.copy(d.ref_final, dst)
                except Exception:
                    dst = d.ref_final
                self._aplicar_voz(dst, nombre)

    def _aplicar_voz(self, ref_path, nombre):
        self.voz_viva.set_referencia(ref_path)
        self.voz_cache = {}          # ignorar caché pre-hecho (era otra voz) -> todo en vivo
        self.custom_voz = True; self.voz_nombre = nombre
        self.settings.setValue("voz_ref_path", ref_path)
        self.settings.setValue("voz_ref_nombre", nombre)
        self._set_voz_banner(f"🎙️  Voz de «{nombre}» aplicada — di cualquier cosa.")
        self.voz_viva.hablar(f"Hola, ahora hablo con la voz de {nombre}.")

    def _aplicar_voz_default(self):
        base = os.path.dirname(os.path.abspath(__file__))
        ref = os.path.join(base, "voz_referencia.wav")
        if os.path.exists(ref):
            self.voz_viva.set_referencia(ref)
        self.custom_voz = False; self.voz_nombre = ""
        self.settings.remove("voz_ref_path"); self.settings.remove("voz_ref_nombre")
        self._cargar_voz_cache()     # restaurar el caché pre-hecho de tu voz original
        self._set_voz_banner("🎙️  Tu voz original — di cualquier palabra o frase.")

    def _voz_estado(self, s):
        if s == "hablando":
            self._set_voz_banner("🔊  Hablando con tu voz…")
        else:
            self._set_voz_banner("🎙️  Tu voz lista — di cualquier palabra o frase.")

    def _set_voz_banner(self, text):
        if getattr(self, "voz_banner", None) is None:
            return
        self.voz_banner.setStyleSheet("background:#dcfce7; color:#166534; padding:8px 14px; "
                                      "border-bottom:1px solid #86efac; font-size:12px; font-weight:600;")
        self.voz_banner.setText(text); self.voz_banner.show()

    # -------- persistencia --------
    def _cargar_board(self):
        raw = self.settings.value("board")
        base = {k: [v[0], v[1], [list(it) for it in v[2]]] for k, v in BASE.items()}
        if raw:
            try:
                d = json.loads(raw)
                if isinstance(d, dict) and d:
                    return d
            except Exception:
                pass
        return base

    def _guardar(self):
        self.settings.setValue("board", json.dumps(self.board))
        self.settings.setValue("sayOnTap", self.say_on_tap)

    # -------- voz --------
    def _setup_tts(self):
        self.tts = None
        self.voice_warn = False
        engines = [e for e in QTextToSpeech.availableEngines() if e != "mock"]
        # buscar un motor con locale en español
        for eng in engines:
            try:
                t = QTextToSpeech(eng)
            except Exception:
                continue
            es = [l for l in t.availableLocales() if l.language() == QLocale.Language.Spanish]
            if es:
                t.setLocale(es[0]); self.tts = t; return
        # ninguno con español -> usar el primero disponible y avisar
        if engines:
            self.tts = QTextToSpeech(engines[0])
            self.voice_warn = True

    def _cargar_voz_cache(self):
        """Carga la caché de audio (tu voz clonada). Si existe, se usa en vez de SAPI."""
        self.voz_cache = {}
        self.voz_sr = 24000
        try:
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voz_cache")
            mani = os.path.join(base, "manifest.json")
            if os.path.exists(mani):
                with open(mani, encoding="utf-8") as f:
                    d = json.load(f)
                self.voz_sr = d.get("sr", 24000)
                for w, fn in d.get("words", {}).items():
                    p = os.path.join(base, fn)
                    if os.path.exists(p):
                        self.voz_cache[w] = p
        except Exception:
            self.voz_cache = {}
        if self.voz_cache:
            self.voice_warn = False   # usamos tu voz clonada; no hace falta avisar de SAPI

    def _play_wav(self, path):
        if winsound and path:
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    def _concat_frase(self, palabras):
        """Une los clips de tu voz de cada palabra en un solo WAV (con pausas) y lo reproduce."""
        paths = [self.voz_cache[w] for w in palabras if w in self.voz_cache]
        if not paths:
            return None
        out = os.path.join(tempfile.gettempdir(), "caa_frase.wav")
        try:
            params, gap = None, b""
            with wave.open(out, "wb") as w_out:
                for k, p in enumerate(paths):
                    with wave.open(p, "rb") as w_in:
                        if params is None:
                            params = w_in.getparams()
                            w_out.setparams(params)
                            gap = (b"\x00\x00" * params.nchannels) * int(params.framerate * 0.07)
                        w_out.writeframes(w_in.readframes(w_in.getnframes()))
                    if k < len(paths) - 1:
                        w_out.writeframes(gap)
            return out
        except Exception:
            return None

    def _decir_palabra(self, txt):
        """Feedback al tocar. Prioridad: caché (instantáneo) > voz en vivo (Chatterbox) > SAPI."""
        if txt in self.voz_cache:
            self._play_wav(self.voz_cache[txt])
        elif self.voz_viva and self.voz_viva_ok:
            self.voz_viva.hablar(txt)
        elif self.tts:
            self.tts.stop(); self.tts.setRate(-0.1); self.tts.say(txt)

    def _decir_frase(self):
        """Dice TODA la frase. En vivo (Chatterbox) = natural y cualquier palabra; si no, caché/SAPI."""
        palabras = [s[1] for s in self.sentence]
        if not palabras:
            return
        texto = " ".join(palabras)
        # 1) voz en vivo Chatterbox: frase completa, natural, cualquier palabra
        if self.voz_viva and self.voz_viva_ok:
            self.voz_viva.hablar(texto)
            return
        # 2) sin GPU: encadenar la caché si cubre todo
        if self.voz_cache and all(w in self.voz_cache for w in palabras):
            p = self._concat_frase(palabras)
            if p:
                self._play_wav(p)
                return
        # 3) SAPI
        if self.tts:
            self.tts.stop(); self.tts.setRate(-0.1); self.tts.say(texto)
        elif self.voz_cache:
            p = self._concat_frase(palabras)
            if p:
                self._play_wav(p)

    def hablar(self, text):   # compatibilidad (fallback SAPI)
        if not text or not self.tts:
            return
        self.tts.stop()
        self.tts.setRate(-0.1)
        self.tts.say(text)

    # -------- interfaz --------
    def _ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # barra superior: frase + acciones
        top = QFrame(); top.setObjectName("topbar")
        tl = QHBoxLayout(top); tl.setContentsMargins(14, 10, 14, 10); tl.setSpacing(10)
        self.frase_area = QScrollArea(); self.frase_area.setObjectName("frasearea")
        self.frase_area.setWidgetResizable(True); self.frase_area.setFixedHeight(84)
        self.frase_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.frase_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frase_host = QWidget(); self.frase_lay = QHBoxLayout(self.frase_host)
        self.frase_lay.setContentsMargins(8, 6, 8, 6); self.frase_lay.setSpacing(8)
        self.frase_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.frase_placeholder = QLabel("Toca los dibujos para hablar…"); self.frase_placeholder.setObjectName("phrasePH")
        self.frase_lay.addWidget(self.frase_placeholder); self.frase_lay.addStretch()
        self.frase_area.setWidget(self.frase_host)
        self.frase_area.mousePressEvent = lambda e: self._decir_frase()
        tl.addWidget(self.frase_area, 1)
        for txt, ico, obj, fn in [("Hablar", "🔊", "speak", self._decir_frase),
                                  ("Borrar", "⌫", "back", self._borrar), ("Vaciar", "🗑️", "clear", self._vaciar)]:
            b = QPushButton(f"{ico}\n{txt}"); b.setObjectName(obj); b.setFixedSize(92, 64)
            b.clicked.connect(fn); tl.addWidget(b)
        root.addWidget(top)

        # banner de voz (se actualiza según el estado: cargando / lista / hablando)
        self.voz_banner = QLabel(""); self.voz_banner.setWordWrap(True); self.voz_banner.hide()
        root.addWidget(self.voz_banner)
        if self.voz_cache:
            self._set_voz_banner(f"🎙️  Tu voz · {len(self.voz_cache)} palabras")
        elif self.voice_warn:
            self.voz_banner.setObjectName("warn")
            self.voz_banner.setStyleSheet("")
            self.voz_banner.setText("🔊  No hay voz en español instalada; se usará otra voz. "
                                    "Configuración → Hora e idioma → Voz para añadir una.")
            self.voz_banner.show()

        # categorías
        self.cats_area = QScrollArea(); self.cats_area.setObjectName("catsarea"); self.cats_area.setFixedHeight(56)
        self.cats_area.setWidgetResizable(True); self.cats_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cats_host = QWidget(); self.cats_lay = QHBoxLayout(self.cats_host)
        self.cats_lay.setContentsMargins(12, 8, 12, 8); self.cats_lay.setSpacing(8); self.cats_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.cats_area.setWidget(self.cats_host); root.addWidget(self.cats_area)

        # rejilla
        self.grid_area = QScrollArea(); self.grid_area.setObjectName("gridarea"); self.grid_area.setWidgetResizable(True)
        self.grid_host = QWidget(); self.grid_lay = QGridLayout(self.grid_host)
        self.grid_lay.setContentsMargins(16, 16, 16, 16); self.grid_lay.setSpacing(12)
        self.grid_area.setWidget(self.grid_host); root.addWidget(self.grid_area, 1)

        # barra inferior
        bottom = QFrame(); bottom.setObjectName("bottom")
        bl = QHBoxLayout(bottom); bl.setContentsMargins(14, 8, 14, 8)
        self.cb_say = QCheckBox("Decir cada palabra al tocar"); self.cb_say.setChecked(self.say_on_tap)
        self.cb_say.toggled.connect(self._toggle_say)
        bl.addWidget(self.cb_say); bl.addStretch()
        self.btn_voz = QPushButton("🎤 Voz"); self.btn_voz.setObjectName("edit"); self.btn_voz.clicked.connect(self._abrir_dialogo_voz)
        bl.addWidget(self.btn_voz)
        self.btn_edit = QPushButton("✏️ Editar tablero"); self.btn_edit.setObjectName("edit"); self.btn_edit.clicked.connect(self._toggle_edit)
        bl.addWidget(self.btn_edit)
        sign = QLabel("Mi Tablero · KALEVI LATVA AIJO ALEGRIA"); sign.setObjectName("sign"); bl.addWidget(sign)
        root.addWidget(bottom)

    # -------- render --------
    def _render_cats(self):
        while self.cats_lay.count():
            it = self.cats_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for key, (nombre, color, _items) in self.board.items():
            b = QPushButton(nombre); b.setObjectName("cat"); b.setCheckable(True)
            b.setChecked(key == self.cat)
            estilo = f"QPushButton#cat {{ background:{color}; border:2px solid {'#1f2937' if key==self.cat else 'transparent'}; }}"
            b.setStyleSheet(estilo)
            b.clicked.connect(lambda _=False, k=key: self._set_cat(k))
            self.cats_lay.addWidget(b)
        self.cats_lay.addStretch()

    def _cols(self):
        w = self.grid_area.viewport().width()
        return max(2, min(7, w // 150))

    def _render_grid(self):
        while self.grid_lay.count():
            it = self.grid_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        nombre, color, items = self.board[self.cat]
        cols = self._cols()
        for i, (emo, txt) in enumerate(items):
            tile = Tile(emo, txt, color)
            tile.set_edit(self.editing)
            tile.clicked.connect(lambda e=emo, t=txt: self._add_word(e, t))
            tile.eliminar.connect(lambda idx=i: self._del_item(idx))
            self.grid_lay.addWidget(tile, i // cols, i % cols)
        if self.editing:
            add = Tile("➕", "Añadir", "#ffffff")
            add.setStyleSheet("#tile { background:#fff; border:3px dashed #cbd5e1; border-radius:18px; }")
            add.clicked.connect(self._abrir_dialogo)
            self.grid_lay.addWidget(add, len(items) // cols, len(items) % cols)

    def _render_frase(self):
        while self.frase_lay.count():
            it = self.frase_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if not self.sentence:
            self.frase_lay.addWidget(self.frase_placeholder)
            self.frase_placeholder.show()
        else:
            for emo, txt in self.sentence:
                chip = QFrame(); chip.setObjectName("chip")
                c = QVBoxLayout(chip); c.setContentsMargins(6, 4, 6, 4); c.setSpacing(0)
                el = QLabel(emo); el.setAlignment(Qt.AlignmentFlag.AlignCenter); el.setFont(QFont(EMOJI_FONT, 18)); el.setStyleSheet("background:transparent;border:none;")
                tl = QLabel(txt); tl.setAlignment(Qt.AlignmentFlag.AlignCenter); tl.setStyleSheet("background:transparent;border:none;font-size:11px;font-weight:600;color:#1f2937;")
                c.addWidget(el); c.addWidget(tl)
                self.frase_lay.addWidget(chip)
        self.frase_lay.addStretch()

    # -------- acciones --------
    def _add_word(self, emo, txt):
        self.sentence.append((emo, txt))
        self._render_frase()
        if self.say_on_tap:
            self._decir_palabra(txt)

    def _borrar(self):
        if self.sentence:
            self.sentence.pop(); self._render_frase()

    def _vaciar(self):
        self.sentence = []; self._render_frase()

    def _set_cat(self, key):
        self.cat = key; self._render_cats(); self._render_grid()

    def _toggle_say(self, on):
        self.say_on_tap = on; self._guardar()

    def _toggle_edit(self):
        self.editing = not self.editing
        self.btn_edit.setText("✅ Listo" if self.editing else "✏️ Editar tablero")
        self.btn_edit.setStyleSheet("QPushButton#edit { background:#4f46e5; color:#fff; }" if self.editing else "")
        self._render_grid()

    def _del_item(self, idx):
        items = self.board[self.cat][2]
        if 0 <= idx < len(items):
            del items[idx]; self._guardar(); self._render_grid()

    def _abrir_dialogo(self):
        d = DialogoAnadir(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            w = d.word.text().strip()
            if w:
                self.board[self.cat][2].append([d.emoji, w]); self._guardar(); self._render_grid()
                self._empaquetar_palabra(w)   # generar y guardar en TU voz (si hay GPU)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._render_grid()


ESTILO = """
* { font-family: 'Segoe UI'; }
QWidget { background: #f4f6fb; color: #1f2937; font-size: 13px; }
QFrame#topbar { background: #ffffff; border-bottom: 2px solid #e5e7eb; }
QScrollArea#frasearea { background: #f9fafb; border: 2px solid #e5e7eb; border-radius: 14px; }
QScrollArea#frasearea > QWidget > QWidget { background: transparent; }
QLabel#phrasePH { color: #6b7280; font-size: 16px; background: transparent; }
QFrame#chip { background: #ffffff; border: 2px solid #e5e7eb; border-radius: 12px; }
QPushButton#speak { background: #16a34a; color: #fff; border: none; border-radius: 14px; font-weight: 800; font-size: 13px; }
QPushButton#speak:hover { background: #15803d; }
QPushButton#back { background: #f59e0b; color: #fff; border: none; border-radius: 14px; font-weight: 800; font-size: 13px; }
QPushButton#back:hover { background: #d97706; }
QPushButton#clear { background: #ef4444; color: #fff; border: none; border-radius: 14px; font-weight: 800; font-size: 13px; }
QPushButton#clear:hover { background: #dc2626; }
QLabel#warn { background: #fef9c3; color: #854d0e; padding: 8px 14px; border-bottom: 1px solid #fde047; font-size: 12px; }
QScrollArea#catsarea, QScrollArea#gridarea { background: #f4f6fb; border: none; }
QScrollArea#catsarea { background: #ffffff; border-bottom: 2px solid #e5e7eb; }
QScrollArea#catsarea > QWidget > QWidget, QScrollArea#gridarea > QWidget > QWidget { background: transparent; }
QPushButton#cat { border-radius: 16px; padding: 6px 18px; font-weight: 700; font-size: 14px; color: #1f2937; }
QPushButton#del { background: #ef4444; color: #fff; border: 2px solid #fff; border-radius: 13px; font-weight: 900; }
QPushButton#del:hover { background: #dc2626; }
QFrame#bottom { background: #ffffff; border-top: 2px solid #e5e7eb; }
QPushButton#edit { background: #fff; border: 2px solid #e5e7eb; border-radius: 12px; padding: 9px 14px; font-weight: 700; }
QPushButton#edit:hover { background: #f3f4f6; }
QLabel#sign { color: #9ca3af; font-size: 11px; padding-left: 12px; }
QCheckBox { font-weight: 600; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 2px solid #cbd5e1; background: #fff; }
QCheckBox::indicator:checked { background: #4f46e5; border-color: #4f46e5; }
QLineEdit { padding: 12px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 15px; background: #fff; }
QDialog { background: #ffffff; }
QPushButton { border: 2px solid #e5e7eb; border-radius: 10px; padding: 9px 14px; font-weight: 700; background: #fff; }
QPushButton#emo { border-radius: 8px; padding: 0; }
QPushButton#emo:checked { background: #c7d2fe; border-color: #4f46e5; }
QPushButton#primary { background: #4f46e5; color: #fff; border-color: #4f46e5; }
"""


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO)
    v = Tablero()
    v.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
