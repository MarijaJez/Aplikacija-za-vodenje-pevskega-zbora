<div>
    <h2>{{pesem.naslov}}</h2>
    <p><strong>Avtor:</strong> {{pesem.avtor or '-'}}</p>
    <p><strong>Notni list:</strong> 
        % if pesem.note:
            <a href=\"{{pesem.note}}\" target=\"_blank\">Odpri PDF</a>
        % end
    </p>
    
    <h3>Ocene:</h3>
    <table>
        <thead>
            <tr>
                <th>Oseba</th>
                <th>Ocena</th>
                <th>Komentar</th>
            </tr>
        </thead>
        <tbody>
        % for ocena in ocene:
            <tr>
                <td>{{ocena.oseba_id}}</td>
                <td>{{ocena.ocena}}</td>
                <td>{{ocena.komentar or '-'}}</td>
            </tr>
        % end
        </tbody>
    </table>
    
    <h3>Dodaj oceno:</h3>
    <form method=\"post\">
        <select name=\"id_osebe\" required>
        % for oseba in osebe:
            <option value=\"{{oseba.id_osebe}}\">{{oseba.ime}} {{oseba.priimek}}</option>
        % end
        </select>
        <select name=\"ocena\" required>
        % for val in rating_values:
            <option value=\"{{val}}\">{{val}}</option>
        % end
        </select>
        <textarea name=\"komentar\"></textarea>
        <button type=\"submit\">Shrani oceno</button>
    </form>
</div>
