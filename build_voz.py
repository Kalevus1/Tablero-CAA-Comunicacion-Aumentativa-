# -*- coding: utf-8 -*-
"""
Genera la CACHÉ de voz del Tablero CAA con TU voz (Chatterbox).
Corre UNA vez en el entorno con GPU (.venv_chatter):

    ../Voz-Lab/.venv_chatter/Scripts/python.exe build_voz.py

Estrategia robusta (evita recortes y alucinaciones):
  · GENERAR y VERIFICAR con Whisper comparando el TEXTO (no contando sílabas):
    - Si lo que oye Whisper (sin tildes/espacios) ES la palabra -> se deja COMPLETA.
    - Si hay texto EXTRA después -> se corta justo donde termina la palabra (en el silencio).
    - Si Whisper se desvía -> se REGENERA (otra semilla), varias veces.
  · Rebeldes cortas que fallan solas (no, ver): portador "{w}, digo." y se extrae la 1ª.
  · limpiar_cola quita burst final tipo respiración/"tsh". fade in/out + normalizado.
"""
import os, json, unicodedata
import numpy as np
import soundfile as sf
import torch, torchaudio
import whisper
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

from tablero_comunicacion import BASE

REF = "voz_referencia2.wav" if os.path.exists("voz_referencia2.wav") else "voz_referencia.wav"
OUT = "voz_cache"
os.makedirs(OUT, exist_ok=True)
print("Referencia:", REF)

KW = dict(language_id="es", audio_prompt_path=REF, exaggeration=0.5, cfg_weight=0.5, temperature=0.5)

words, seen = [], set()
for _k, (_n, _c, items) in BASE.items():
    for _emo, txt in items:
        if txt not in seen:
            seen.add(txt); words.append(txt)
print(f"Palabras únicas a generar: {len(words)}")


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s if c.isalnum())


def gen_once(model, text):
    try:
        w = model.generate(text, **KW)
        return (w.cpu() if w.is_cuda else w).squeeze().numpy().astype(np.float32)
    except Exception:
        return None


def wwords(arr, sr, wmodel):
    a16 = torchaudio.functional.resample(torch.from_numpy(arr).unsqueeze(0), sr, 16000).squeeze(0).numpy()
    res = wmodel.transcribe(a16, language="es", word_timestamps=True,
                            condition_on_previous_text=False, temperature=0.0, fp16=True)
    return [x for seg in res.get("segments", []) for x in seg.get("words", [])]


def analizar(ws, target):
    """Compara el texto oído con la palabra. -> ('completo'|'cortar'|'malo', k)."""
    tn = norm(target); cum = ""
    for k, wd in enumerate(ws):
        cum += norm(wd.get("word", ""))
        if cum == tn:
            return ("completo", k) if k == len(ws) - 1 else ("cortar", k)
        if not tn.startswith(cum):
            return ("malo", None)
    return ("malo", None)


def bound(arr, ws, k_last, sr):
    """Acota el audio a la palabra: quita pop/aire antes del inicio y cola/basura tras el fin."""
    s = max(0, int((ws[0]["start"] - 0.03) * sr))
    e_t = ws[k_last]["end"] + 0.12
    if k_last + 1 < len(ws):                 # hay algo después: no invadirlo
        e_t = min(e_t, (ws[k_last]["end"] + ws[k_last + 1]["start"]) / 2)
    return arr[s:min(int(e_t * sr), len(arr))]


def limpiar_cola(arr, sr):
    thr = max(0.015, np.max(np.abs(arr)) * 0.06)
    voiced = np.abs(arr) > thr
    n = len(arr); i = n - 1
    while i > 0 and not voiced[i]:
        i -= 1
    tail_end = i
    minsil = int(0.09 * sr); maxtail = int(0.22 * sr)
    j = i; sil = 0
    while j > 0:
        if not voiced[j]:
            sil += 1
            if sil >= minsil:
                if tail_end - (j + sil) < maxtail:
                    return arr[:j + int(0.02 * sr)]
                break
        else:
            sil = 0
        j -= 1
    return arr


def recortar_y_fade(arr, sr):
    thr = max(0.015, np.max(np.abs(arr)) * 0.06)
    idx = np.where(np.abs(arr) > thr)[0]
    if len(idx) == 0:
        return arr
    arr = arr[max(0, idx[0] - int(0.01 * sr)):min(len(arr), idx[-1] + int(0.02 * sr))].copy()
    f = int(sr * 0.018)   # fade 18ms (evita pops de arranque)
    if len(arr) > 2 * f:
        r = np.linspace(0, 1, f, dtype=np.float32); arr[:f] *= r; arr[-f:] *= r[::-1]
    return arr


def build_word(model, wmodel, w, sr):
    """Genera varias veces y elige el mejor recorte DENTRO de un rango de duración sano
    (los timestamps de Whisper varían: a veces recortan de más, a veces dejan alucinaciones)."""
    n = len(w.split())
    MIN_ABS = int(sr * 0.20)
    MIN_OK = int(sr * 0.28)
    MAX_OK = int(sr * (0.55 + 0.45 * n))          # ~1.0s (1 palabra), ~1.45s (2 palabras)
    verificados, best = [], []
    for t in [w + "."] * 5 + [f"{w}, digo."] * 5:
        arr = gen_once(model, t)
        if arr is None or len(arr) < sr * 0.1:
            continue
        ws = wwords(arr, sr, wmodel)
        if not ws:
            continue
        est, k = analizar(ws, w)
        if est in ("completo", "cortar"):
            b = bound(arr, ws, k, sr)
            verificados.append((len(b), b, est))
            if MIN_OK <= len(b) <= MAX_OK:        # verificada y en rango -> aceptar ya
                return b, est
        else:
            b = bound(arr, ws, len(ws) - 1, sr)
            best.append((len(b), b))
    en_rango = [c for c in verificados if MIN_ABS <= c[0] <= MAX_OK]
    if en_rango:
        en_rango.sort(key=lambda c: -c[0]); return en_rango[0][1], en_rango[0][2]
    best = [c for c in best if MIN_ABS <= c[0] <= MAX_OK]
    if best:
        best.sort(key=lambda c: c[0]); return best[0][1], "best"   # no verificada: la más corta sana
    if verificados:                               # nada en rango: la verificada menos mala
        verificados.sort(key=lambda c: c[0])
        if verificados[0][0] >= MIN_ABS:
            return verificados[0][1], "fuera-rango"
    return None, "falla"


# ---- pipeline ROBUSTO: generar la palabra 3 veces y extraer la del medio ----
# La repetición estabiliza la pronunciación (una palabra suelta es inestable) y valida
# (3 repeticiones consistentes = correcta). Se extrae la del medio (rodeada de pausas = limpia).
def _instancias(ws, w):
    tn = norm(w); res = []; cum = ""; start = None
    for k, wd in enumerate(ws):
        t = norm(wd.get("word", ""))
        if start is None:
            start = k; cum = t
        else:
            cum += t
        if cum == tn:
            res.append((start, k)); cum = ""; start = None
        elif not tn.startswith(cum):
            cum = t; start = k
            if cum == tn:
                res.append((start, k)); cum = ""; start = None
            elif not tn.startswith(cum):
                cum = ""; start = None
    return res


def _extraer_medio(arr, ws, inst, sr):
    i0, i1 = inst[len(inst) // 2]
    prev_end = ws[i0 - 1]["end"] if i0 > 0 else max(0.0, ws[i0]["start"] - 0.05)
    s = int(((prev_end + ws[i0]["start"]) / 2) * sr)
    if i1 + 1 < len(ws):
        e = int(((ws[i1]["end"] + ws[i1 + 1]["start"]) / 2) * sr)
    else:
        e = int((ws[i1]["end"] + 0.10) * sr)
    return arr[max(0, s):min(e, len(arr))]


def generar_robusto(model, wmodel, w, sr, intentos=4):
    for _ in range(intentos):
        arr = gen_once(model, f"{w}, {w}, {w}.")
        if arr is None:
            continue
        ws = wwords(arr, sr, wmodel)
        inst = _instancias(ws, w)
        if len(inst) >= 3:
            return _extraer_medio(arr, ws, inst, sr), "3x"
        if len(inst) == 2:
            return _extraer_medio(arr, ws, inst + inst[-1:], sr), "2x"
    return build_word(model, wmodel, w, sr)   # fallback al método anterior


def cargar_modelos():
    print("Cargando Chatterbox...")
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    print("Cargando Whisper (small)...")
    wmodel = whisper.load_model("small", device="cuda")
    return model, wmodel, model.sr


def generar_palabra(model, wmodel, w, sr):
    """Genera una palabra en tu voz (pipeline robusto 3x) y devuelve el array final (o None)."""
    arr, modo = generar_robusto(model, wmodel, w, sr)
    if arr is None:
        return None, "falla"
    arr = recortar_y_fade(arr, sr)   # bound() ya limpia el final; NO usar limpiar_cola (parte sílabas)
    arr = arr * (0.95 / (float(np.max(np.abs(arr))) or 1.0))
    return arr, modo


def main():
    model, wmodel, sr = cargar_modelos()
    manifest, fallidas = {}, []
    for i, w in enumerate(words):
        arr, modo = generar_palabra(model, wmodel, w, sr)
        if arr is None:
            fallidas.append(w); print(f"[{i+1}/{len(words)}] {w!r} -> SIN VOZ (SAPI)"); continue
        fn = f"{i:03d}.wav"
        sf.write(os.path.join(OUT, fn), arr, sr, subtype="PCM_16")
        manifest[w] = fn
        print(f"[{i+1}/{len(words)}] {w!r} -> {fn} ({modo}, {len(arr)/sr:.2f}s)")
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"sr": sr, "words": manifest}, f, ensure_ascii=False, indent=1)
    print(f"LISTO -> {OUT}/  ({len(manifest)} con voz, {len(fallidas)} fallidas: {fallidas})")


if __name__ == "__main__":
    main()
