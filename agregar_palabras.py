# -*- coding: utf-8 -*-
"""
Genera TU voz para las palabras NUEVAS que agregaste en el tablero.
Corre en el entorno con GPU (.venv_chatter):

    ../Voz-Lab/.venv_chatter/Scripts/python.exe agregar_palabras.py

Lee el tablero actual (lo que guardó la app en QSettings, incluidas tus palabras nuevas),
busca las que aún NO están en voz_cache/, y solo genera esas. No rehace las existentes.
Después, reabre el tablero y ya hablarán con tu voz.
"""
import os, json
import numpy as np
import soundfile as sf
from PySide6.QtCore import QSettings

import build_voz as bv   # reutiliza el motor (build_word, generar_palabra, cargar_modelos, BASE)

OUT = "voz_cache"
os.makedirs(OUT, exist_ok=True)


def palabras_del_usuario():
    """Todas las palabras del tablero actual: las guardadas por la app + las de BASE."""
    words, seen = [], set()

    def add(txt):
        if txt and txt not in seen:
            seen.add(txt); words.append(txt)

    # 1) tablero guardado por la app (incluye tus palabras nuevas)
    try:
        raw = QSettings("KaleviApps", "TableroCAA").value("board")
        if raw:
            d = json.loads(raw)
            for _k, v in d.items():
                for _emo, txt in v[2]:
                    add(txt)
    except Exception as e:
        print("Aviso: no pude leer el tablero guardado:", e)
    # 2) BASE (por si la app nunca se guardó)
    for _k, (_n, _c, items) in bv.BASE.items():
        for _emo, txt in items:
            add(txt)
    return words


def main():
    words = palabras_del_usuario()
    mani_path = os.path.join(OUT, "manifest.json")
    if os.path.exists(mani_path):
        data = json.load(open(mani_path, encoding="utf-8"))
        manifest = data.get("words", {})
    else:
        manifest = {}

    faltan = [w for w in words if w not in manifest]
    if not faltan:
        print("No hay palabras nuevas: todo el tablero ya tiene tu voz. ✔")
        return
    print(f"Palabras nuevas a generar en tu voz: {faltan}")

    model, wmodel, sr = bv.cargar_modelos()
    # siguiente número de archivo libre
    usados = [int(fn[:3]) for fn in manifest.values() if fn[:3].isdigit()]
    idx = (max(usados) + 1) if usados else 0

    nuevas = 0
    for w in faltan:
        arr, modo = bv.generar_palabra(model, wmodel, w, sr)
        if arr is None:
            print(f"  {w!r} -> no se pudo (usará voz del sistema)"); continue
        fn = f"{idx:03d}.wav"; idx += 1
        sf.write(os.path.join(OUT, fn), arr, sr, subtype="PCM_16")
        manifest[w] = fn; nuevas += 1
        print(f"  {w!r} -> {fn} ({modo}, {len(arr)/sr:.2f}s)")

    json.dump({"sr": sr, "words": manifest}, open(mani_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"LISTO: {nuevas} palabra(s) nueva(s) con tu voz. Reabre el tablero.")


if __name__ == "__main__":
    main()
