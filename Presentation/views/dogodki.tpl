<table>
    <thead>
        <tr>
            <th>Datum</th>
            <th>Vrsta dogodka</th>
            <th>Naziv</th>
            <th>Podrobnosti</th>
        </tr>
    </thead>
    <tbody>
    % for dogodek in dogodki:
        <tr>
            <td>{{dogodek:.datum']}}</td>
            <td>{{dogodek:.vrsta_dogodka'] or '-'}}</td>
            <td>{{dogodek:.naziv_dogodka']}}</td>
            <td><a href="/dogodek/{{dogodek:.id_dogodka']}}">Ogled</a></td>
        </tr>
    % end
    </tbody>
</table>

