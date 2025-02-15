from PySide2 import QtWidgets

from Code.Base import Game
from Code.QT import Colocacion
from Code.QT import Columnas
from Code.QT import Grid
from Code.QT import Iconos
from Code.QT import QTVarios
from Code.Themes import Themes


class WDBMoveAnalysis(QTVarios.WDialogo):
    """
    The WDBMoveAnalysis class is used to show outputs of the move analysis

    Args:
        w_parent: The parent window
        *li_output_dic: Data to be displayed in the grid
        *titulo (str): Window title
        *missing_tags_output (str): Showing the list of games with no tags

    """

    def __init__(self, w_parent, li_output_dic, titulo, missing_tags_output):
        icono = Iconos.Tacticas()
        extparam = "themeanalysis"
        QTVarios.WDialogo.__init__(self, w_parent, titulo, icono, extparam)
        self.owner = w_parent
        self.li_output_dic = li_output_dic

        # Lista
        o_columns = Columnas.ListaColumnas()
        o_columns.nueva("theme", _("Theme"), 120, centered=True)
        o_columns.nueva("games", _("Games"), 100, centered=True)
        o_columns.nueva("centipawns_lost", _("Centipawns lost"), 104, centered=True)
        o_columns.nueva("count", _("Occurrences"), 80, centered=True)
        symbol = "\u2605"
        o_columns.nueva("occ_game", symbol + " " + _("Occ / game"), 90, centered=True)
        o_columns.nueva("loss_game", symbol + " " + _("Loss / game"), 90, centered=True)

        self.grid = grid = Grid.Grid(self, o_columns, xid=False, siSelecFilas=True, siSeleccionMultiple=True)
        self.register_grid(grid)

        self.status = QtWidgets.QStatusBar(self)
        self.status.setFixedHeight(22)
        self.status.showMessage(" %s %s %s" % (symbol, _("calculated using all games"), missing_tags_output))

        # Colocamos ---------------------------------------------------------------
        ly = Colocacion.V().control(self.grid).control(self.status).margen(1)

        self.setLayout(ly)

        self.restore_video(siTam=True, anchoDefecto=750, altoDefecto=562)

    def terminar(self):
        self.save_video()
        self.accept()

    def grid_num_datos(self, grid):
        return len(self.li_output_dic)

    def grid_dato(self, grid, row, o_column):
        col = o_column.key
        return self.li_output_dic[row][col]


class SelectedGameThemeAnalyzer:
    def __init__(self, w_parent):
        li_sel = w_parent.grid.recnosSeleccionados()
        self.dic_themes = dict()
        self.li_output_dic = []
        self.missing_tags_output = ""
        self.game_count = len(li_sel)
        self.li_games_missing_themes = []
        self.tag_count = 0
        self.themes = Themes.Themes()

        for n, recno in enumerate(li_sel):

            game_has_themes = False
            themes_in_game = []
            my_game: Game.Game = w_parent.dbGames.read_game_recno(recno)
            for move_num, move in enumerate(my_game.li_moves):
                lostp_abs = move.get_points_lost()
                if lostp_abs is not None:
                    for theme in self.themes.get_themes_labels(move):
                        game_has_themes = True
                        self.tag_count += 1
                        lostp_abs = min(move.get_points_lost(), 2000)  # limite para missed checkmate
                        if theme not in self.dic_themes:
                            self.dic_themes[theme] = {"centipawns_lost": 0, "count": 0, "total_time": 0, "games": 0}
                        self.dic_themes[theme]["centipawns_lost"] += lostp_abs
                        self.dic_themes[theme]["count"] += 1
                        if theme not in themes_in_game:
                            themes_in_game.append(theme)
                            self.dic_themes[theme]["games"] += 1

            if not game_has_themes:
                # self.li_games_missing_themes.append("# %s (%s-%s)" % (recno + 1, my_game.get_tag("White"),
                #                                                  my_game.get_tag("Black")))
                self.li_games_missing_themes.append("#%s" % (recno + 1,))

        for key, value in sorted(self.dic_themes.items(), key=lambda i: i[1]["count"], reverse=True):
            self.li_output_dic.append(
                {
                    "theme": key,
                    "games": "%s (%s" % (value["games"], int(100 * value["games"] / self.game_count)) + "%)",
                    "centipawns_lost": value["centipawns_lost"],
                    "count": value["count"],
                    "occ_game": round(value["count"] / self.game_count, 2),
                    "loss_game": int(value["centipawns_lost"] / self.game_count),
                }
            )

        if len(self.li_games_missing_themes):
            self.missing_tags_output = " -  %s: %s" % (_("Games without themes"), " ,".join(self.li_games_missing_themes))

        self.title = "%s - %d %s  (%d %s)" % (
            _("Statistics on tactical themes"),
            self.game_count,
            _("games analysed"),
            self.tag_count,
            _("tags found"),
        )
