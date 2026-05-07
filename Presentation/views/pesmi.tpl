<section class="filter-bar">
    <form method="get" action="/pesmi">
        <label for="kategorija">Filtriraj po kategoriji:</label>
        <select id="kategorija" name="kategorija">
            <option value="">Vse kategorije</option>
            % for kategorija in kategorije:
                <option value="{{kategorija.id_kategorije}}" {{'selected' if izbrana == kategorija.id_kategorije else ''}}>{{kategorija.naziv}}</option>
            % end
        </select>
        <button type="submit">Filtriraj</button>
    </form>
</section>

<table>
    <thead>
        <tr>
            <th>Naslov</th>
            <th>Avtor</th>
            <th>Kategorije</th>
            <th>Note</th>
        </tr>
    </thead>
    <tbody>
    % for pesem in pesmi:
        <tr>
            <td><a href="/pesem/{{pesem.id_pesmi}}">{{pesem.naslov}}</a></td>
            <td>{{pesem.avtor or '-'}}</td>
            <td>{{pesem.get('kategorije', '-') or '-'}}</td>
            <td>
                % if pesem.note:
                    <a href="{{pesem.note}}" target="_blank">Odpri note</a>
                % else:
                    -
                % end
            </td>
        </tr>
    % end
    </tbody>
</table>

