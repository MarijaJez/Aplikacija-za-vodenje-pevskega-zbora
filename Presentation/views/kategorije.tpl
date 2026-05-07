<table>
    <thead>
        <tr>
            <th>Naziv</th>
        </tr>
    </thead>
    <tbody>
    % for kategorija in kategorije:
        <tr>
            <td>{{kategorija.naziv}}</td>
        </tr>
    % end
    </tbody>
</table>
