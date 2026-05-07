<section class="detail-block">
    <h2>{{dogodek.naziv_dogodka}}</h2>
    <p><strong>Datum:</strong> {{dogodek.datum}}</p>
    <p><strong>Vrsta:</strong> {{dogodek.vrsta_dogodka or '-'}}</p>
    <p><a class="button" href="/prisotnost/{{dogodek.id_dogodka}}">Uredi prisotnost</a></p>
</section>

<section class="detail-block">
    <h3>Program dogodka</h3>
    % if program:
        <table>
            <thead>
                <tr>
                    <th>Vrstni red</th>
                    <th>Pesem</th>
                    <th>Avtor</th>
                    <th>Note</th>
                </tr>
            </thead>
            <tbody>
            % for vrstica in program:
                <tr>
                    <td>{{vrstica.vrstni_red or '-'}}</td>
                    <td>{{vrstica.naslov}}</td>
                    <td>{{vrstica.avtor or '-'}}</td>
                    <td>
                        % if vrstica.note:
                            <a href="{{vrstica.note}}" target="_blank">Odpri note</a>
                        % else:
                            -
                        % end
                    </td>
                </tr>
            % end
            </tbody>
        </table>
    % else:
        <p>Za dogodek ni določenega programa.</p>
    % end
</section>

<section class="detail-block">
    <h3>Prisotnost</h3>
    % if prisotnost:
        <table>
            <thead>
                <tr>
                    <th>Član</th>
                    <th>Prisotnost</th>
                </tr>
            </thead>
            <tbody>
            % for vrstica in prisotnost:
                <tr>
                    <td>{{vrstica.ime}} {{vrstica.priimek}}</td>
                    <td>{{'Prisoten' if vrstica.prisotnost else 'Odsoten'}}</td>
                </tr>
            % end
            </tbody>
        </table>
    % else:
        <p>Za ta dogodek ni unesenih podatkov o prisotnosti.</p>
    % end
</section>

