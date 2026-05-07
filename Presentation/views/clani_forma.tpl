<form method=\"post\">
    <input type=\"text\" name=\"ime\" placeholder=\"Ime\" required>
    <input type=\"text\" name=\"priimek\" placeholder=\"Priimek\" required>
    <input type=\"date\" name=\"datum_rojstva\" required>
    <input type=\"email\" name=\"eposta\" placeholder=\"Email\">
    <input type=\"tel\" name=\"telefonska_stevilka\" placeholder=\"Telefon\">
    <select name=\"id_glasu\">
        <option value=\"\">Izberi glas</option>
        % for glas in glasovi:
            <option value=\"{{glas.id_glasu}}\">{{glas.naziv_glasu}}</option>
        % end
    </select>
    <select name=\"id_vloge\">
        <option value=\"\">Izberi vlogo</option>
        % for vloga in vloge:
            <option value=\"{{vloga.id_vloge}}\">{{vloga.naziv}}</option>
        % end
    </select>
    <button type=\"submit\">Shrani</button>
</form>
