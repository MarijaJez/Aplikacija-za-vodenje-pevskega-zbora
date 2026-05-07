<table>
    <thead>
        <tr>
            <th>Ime</th>
            <th>Priimek</th>
            <th>E-pošta</th>
            <th>Telefon</th>
            <th>Glas</th>
            <th>Vloga</th>
        </tr>
    </thead>
    <tbody>
    % for oseba in osebe:
        <tr>
            <td>{{oseba.ime}}</td>
            <td>{{oseba.priimek}}</td>
            <td>{{oseba.eposta or '-'}}</td>
            <td>{{oseba.telefonska_stevilka or '-'}}</td>
            <td>{{oseba.get('glas', '-') or '-'}}</td>
            <td>{{oseba.get('vloga', '-') or '-'}}</td>
        </tr>
    % end
    </tbody>
</table>

