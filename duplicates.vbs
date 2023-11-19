// ==PREPROCESSOR==
// @name "Duplication Remover"
// @author "Fumiaki Taguchi"
// @feature "dragdrop"
// @import "%fb2k_component_path%docs\helpers.txt"
// ==/PREPROCESSOR==

// References
// http://moon.gmobb.jp/renno/cgi/junk.cgi/computer/playlist_filter2.htm

var g_font = gdi.Font("メイリオ", 16, 1);
fb.trace("Remove Start.");


function on_mouse_mbtn_down(x, y, mask) {
    window.ShowConfigure();
}

function on_mouse_lbtn_down(x, y, mask) {
    remove_duplicated_data();
    fb.trace("Removed!");
}

function on_paint(gr) {
    gr.SetTextRenderingHint(5);
    var ww = window.Width;
    var wh = window.Height;
    var txt = "Click to select duplicates";
    gr.DrawString(txt, g_font, RGB(64, 64, 128), 0, 0, ww, wh, 0x11005000);
}

// メタ文字をエスケープ
var regExpEscape = function (str) {
    if (typeof (str) == "string") {
        // return str.replace(/[-\/\\^$*+?.()|\[\]{}]/g, '\\$&').toLowerCase();
        str = str.replace(/[-\/\\^$*+?.()|\[\]{}]/g, '');
        str = str.replace(/[（）［］'’~～\-"”]/g, "");
        str = str.replace("　", " ");
        return str.toLowerCase();;
    } else {
        return str;
    }
};

//アクティブなプレイリストから重複するトラックを除去
// 2016/11/19 Junya Renno
function remove_duplicated_data() {
    // 設定
    var check1 = true; //同じtitle,かつ同じartist,同じdateの曲を除く
    var check2 = true; //同じtitle,かつ同じartistで,違うdateの曲を除く
    var check3 = true; //ほぼ同じtitle,かつ同じartistの曲を除く（instrumental,remix,var）

    // 初期化
    var sorted_list = new Array;
    var delete_items = new Array;
    var tmp_title, tmp_artist, tmp_date, tmp_album, tmp_index;
    var loc = plman.GetPlayingItemLocation();
    // var locitem = loc.PlaylistItemIndex;
    var handles = plman.GetPlaylistItems(plman.ActivePlaylist);
    var re_album = new RegExp('come along|live', 'i');
    var count = plman.PlaylistItemCount(plman.ActivePlaylist);
    if (count <= 0) return;

    // ActivePlaylistから比較用のデータを取り出す
    for (var i = 0; i < count; i++) {
        var pl_tf = fb.TitleFormat("%title% ^^ %artist% ^^ %date% ^^ %albumyear% ^^ %album%").EvalWithMetadb(handles.item(i))
        var pl_el = pl_tf.split(" ^^ ");
        if (pl_el[2] == "?") pl_el[2] = pl_el[3];
        pl_el[2] = pl_el[2].slice(0, 4);
        sorted_list[i] = [regExpEscape(pl_el[0]), i, pl_el[1], pl_el[2], regExpEscape(pl_el[4])];
    }

    // title&dateでソート
    sorted_list.sort(function (a, b) {
        if (a[0] > b[0]) return 1;
        if (a[0] < b[0]) return -1;

        // albumyear は新しい順、例外アルバムは更に後ろ
        if (re_album.test(b[4])) return -1;
        else if (re_album.test(a[4])) return 1;
        else if (a[3] < b[3]) return 1;
        else if (a[3] > b[3]) return -1;
        return 0;
    });

    // 実際の判定処理
    for (var i = 0; i < count; i++) {
        var re = new RegExp('^' + tmp_title, 'i');
        var re2 = new RegExp('live|tv|short|single|remix| mix|wo | edit| ver| style|another| version|recording', 'i');
        var re_inst = new RegExp('instrumental|without vocals|backing track|karaoke|inst|カラオケ|off vocal|without |vocalless', 'i');
        var re_remaster = new RegExp('remaster', 'i');
        if (re_inst.test(sorted_list[i][0])) {
            fb.trace("check inst: " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3] + " " + sorted_list[i][4]);
            delete_items.push(sorted_list[i][1]);
        } else if (sorted_list[i][0] == tmp_title) {
            // title 完全一致
            if (sorted_list[i][2] == tmp_artist) {
                if (re_album.test(sorted_list[i][4])) {
                    fb.trace("check album: " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3] + " " + sorted_list[i][4]);
                    delete_items.push(sorted_list[i][1]);
                } else if (check1 && sorted_list[i][3] == tmp_date) {
                    fb.trace("check1 * " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3]);
                    delete_items.push(sorted_list[i][1]);
                } else if (check2) {
                    fb.trace("check2: " + tmp_title + " " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3]);
                    delete_items.push(sorted_list[i][1]);
                }
            }
        } else if (re.test(sorted_list[i][0]) && sorted_list[i][2] == tmp_artist && re_remaster.test(sorted_list[i][0])) {
            // Remaster がタイトルに含まれている場合はそちらを優先
            fb.trace("check remaster: " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3]);
            delete_items.push(tmp_index);
            tmp_index = sorted_list[i][1];
            tmp_date = sorted_list[i][3];
            tmp_album = sorted_list[i][4];
        } else if (check3 && sorted_list[i][2] == tmp_artist && re.test(sorted_list[i][0]) && re2.test(sorted_list[i][0])) {
            fb.trace("check3 * " + sorted_list[i][0] + " " + sorted_list[i][2] + " " + sorted_list[i][3]);
            delete_items.push(sorted_list[i][1]);
        } else {
            tmp_title = sorted_list[i][0];
            tmp_index = sorted_list[i][1];
            tmp_artist = sorted_list[i][2];
            tmp_date = sorted_list[i][3];
            tmp_album = sorted_list[i][4];
        }
    }
    // プールしておいた曲を選択
    plman.SetPlaylistSelection(plman.ActivePlaylist, delete_items, true);

    // 選択曲を除去
    // plman.RemovePlaylistSelection(plman.ActivePlaylist);

    // list のクリア
    sorted_list = null;

}