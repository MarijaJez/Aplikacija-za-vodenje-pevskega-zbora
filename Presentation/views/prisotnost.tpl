<div>
    <h2>Prisotnost za: {{dogodek.naziv_dogodka}}</h2>
    <p><strong>Datum:</strong> {{dogodek.datum}}</p>
    <p><strong>Vrsta:</strong> {{dogodek.vrsta_dogodka or '-'}}</p>
    
    <form method=\"post\">
        <table>
            <thead>
                <tr>
                    <th>Oseba</th>
                    <th>Prisoten</th>
                </tr>
            </thead>
            <tbody>
            % for vrstica in prisotnost:
                <tr>
                    <td>{{vrstica.ime}} {{vrstica.priimek}}</td>
                    <td>
                        <input type=\"hidden\" name=\"prisotnost_{{vrstica.id_osebe}}\" value=\"0\">
                        <input type=\"checkbox\" name=\"prisotnost_{{vrstica.id_osebe}}\" value=\"1\" {{'checked' if vrstica.prisotnost else ''}}>
                    </td>
                </tr>
            % end
            </tbody>
        </table>
        <button type=\"submit\">Shrani prisotnost</button>
    </form>
</div>
