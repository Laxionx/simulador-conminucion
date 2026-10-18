"""Las tablas de corrientes y de pasantes con los encabezados en el idioma de la app (los nombres
de las columnas del modelo siguen en español en `conminucion`)."""

from __future__ import annotations

import pandas as pd
from i18n import TEXTS, t


def stream_table(df: pd.DataFrame) -> pd.DataFrame:
    """La tabla de corrientes: cada encabezado del modelo, en el idioma de la app."""
    return df.rename(columns={c: t("tcol." + c) for c in df.columns if "tcol." + c in TEXTS["es"]})


def passing_table(df: pd.DataFrame) -> pd.DataFrame:
    """La tabla de pasantes: el tamiz y cada corriente, con su nombre en el idioma de la app."""
    names = {c: t("tid." + c) for c in df.columns if "tid." + c in TEXTS["es"]}
    return df.rename(columns={**names, "tamiz_um": t("tcol.tamiz_um")})
