"""G6-37: la marca que comprueba si la carpeta de archivos sobrevive a un reinicio."""

from g6_admin import persistencia


def test_marcar_y_comprobar(tmp_path):
    marca = persistencia.marcar(tmp_path / "archivos")
    assert persistencia.comprobar(tmp_path / "archivos") == marca


def test_si_la_carpeta_se_perdio_lo_dice(tmp_path):
    persistencia.marcar(tmp_path)
    (tmp_path / persistencia.NOMBRE_MARCA).unlink()  # Lo que pasa al recrear el contenedor.
    assert persistencia.comprobar(tmp_path) is None
    assert persistencia.comprobar(tmp_path / "no-existe") is None


def test_marca_dañada_cuenta_como_perdida(tmp_path):
    (tmp_path / persistencia.NOMBRE_MARCA).write_text("{roto", encoding="utf-8")
    assert persistencia.comprobar(tmp_path) is None


def test_usa_upload_dir_o_la_carpeta_del_g2():
    assert str(persistencia.carpeta_de_archivos({"UPLOAD_DIR": "/data/archivos"})) == (
        "/data/archivos")
    assert str(persistencia.carpeta_de_archivos({})) == "uploads"


def test_el_comando_sale_con_1_si_no_esta(tmp_path, capsys):
    assert persistencia.main(["comprobar", "--dir", str(tmp_path)]) == 1
    assert persistencia.main(["marcar", "--dir", str(tmp_path)]) == 0
    assert persistencia.main(["comprobar", "--dir", str(tmp_path)]) == 0
    assert "✓" in capsys.readouterr().out
