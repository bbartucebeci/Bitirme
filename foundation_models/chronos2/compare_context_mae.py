"""Build static comparison artifacts without modifying experiment inputs."""
import csv
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dataset_generator.catalog import PROJECT_ROOT, family_for_schema

ROOT = PROJECT_ROOT
SOURCE = None
OUT = None
CONTEXTS = [96, 256, 512, 992]
HEADERS = ['Mode', 'Target', 'Radar type', 'Error level', *[f'L={n}' for n in CONTEXTS], 'Unit']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    global SOURCE,OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='Completed Chronos zero-shot run directory')
    parser.add_argument('--output-dir',type=Path,help='Default: outputs/<dataset_family>/mae_comparison/<run_name>')
    args=parser.parse_args()
    SOURCE=args.source.resolve()
    config = json.loads((SOURCE/'run_config.json').read_text())
    schema='consecutive_future_v2' if config['window_mode']=='boundary' else 'complex_pri_v1'
    family=family_for_schema(schema)
    OUT=(args.output_dir or ROOT/'outputs'/family/'mae_comparison'/SOURCE.name).resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f'Use a fresh output folder: {OUT}')
    OUT.mkdir(parents=True,exist_ok=True)
    original_hash = digest(SOURCE/'metrics.csv')
    with (SOURCE/'metrics.csv').open(newline='') as stream:
        source = list(csv.DictReader(stream))
    assert config['regime'] == 'zero_shot' and config['context_lens'] == CONTEXTS
    assert config['horizon'] == 32 and config['max_test_seqs'] is None
    assert set(config['tasks'])=={'PRI','Frequency','multivariate'}
    assert set(config['profiles'])=={'fixed','varying'}
    assert set(config['radar_types'])=={'stable','jitter','stagger','dwell_and_switch','sliding','sinusoidal','triangular_sliding','markov_agile'}
    assert set(config['error_levels'])=={'clean',*[f'error_lv{i}' for i in range(1,8)]}
    boundary=config['window_mode']=='boundary'
    if boundary:
        assert config['dataset_size']=='1000x1056'
        manifest=json.loads((SOURCE/'test_windows.json').read_text())
        assert manifest['meta']['schema_version']=='consecutive_future_v2'
        assert manifest['meta']['window_mode']=='boundary' and manifest['meta']['horizon_len']==32
    lookup = {}
    checked = 0
    for row in source:
        key = (row['task'], int(row['context_len']), row['profile'], row['radar_type'], row['error_level'])
        assert key not in lookup, f'Duplicate: {key}'
        assert int(row['num_sequences']) == 200 and int(row['valid_pulses_evaluated']) == 6400
        assert int(row['horizon']) == 32
        assert int(row['skipped_short']) == int(row['skipped_no_emitter']) == 0
        detail = SOURCE/row['task']/f"L{row['context_len']}"/row['profile']/'per_sequence'/f"{row['radar_type']}_{row['error_level']}.csv"
        with detail.open(newline='') as stream:
            sequences = list(csv.DictReader(stream))
        assert len(sequences) == 200
        assert {s['sequence_id'] for s in sequences}=={f'seq_{i:04d}' for i in range(800,1000)}
        if boundary:
            assert all(int(s['start'])==1024-int(row['context_len']) for s in sequences)
        metrics = ['mae_pri', 'mae_frequency'] if row['task'] == 'multivariate' else ['mae']
        for metric in metrics:
            value = float(row[metric])
            assert math.isfinite(value) and value >= 0
            assert math.isclose(value, math.fsum(float(s[metric]) for s in sequences)/200,
                                rel_tol=1e-12, abs_tol=1e-10), (key, metric)
            checked += 1
        lookup[key] = row
    expected = set(itertools.product(config['tasks'], CONTEXTS, config['profiles'], config['radar_types'], config['error_levels']))
    assert set(lookup) == expected and len(expected) == 1536
    views, profile_rows = [], {}
    for profile in config['profiles']:
        profile_rows[profile] = []
        for mode, task, target, metric, unit in [
            ('Univariate', 'PRI', 'PRI', 'mae', 'µs'),
            ('Univariate', 'Frequency', 'Frequency', 'mae', 'MHz'),
            ('Multivariate', 'multivariate', 'PRI', 'mae_pri', 'µs'),
            ('Multivariate', 'multivariate', 'Frequency', 'mae_frequency', 'MHz'),
        ]:
            rows = []
            for radar in config['radar_types']:
                for level in config['error_levels']:
                    values = [float(lookup[(task, length, profile, radar, level)][metric]) for length in CONTEXTS]
                    rows.append([radar, level, *values])
                    profile_rows[profile].append([mode, target, radar, level, *values, unit])
            views.append((profile, mode, target, unit, rows))

    protocol='consecutive future v2' if boundary else 'observed future v1'
    md = [f'# {family}: Chronos-2 zero-shot MAE karşılaştırması', '',f'Protokol: {protocol}.', '',
          'L = 96, 256, 512, **992**. H = 32. Her hücre 200 test sekansının MAE ortalamasıdır.',
          ('Her context uzunluğu 1024 gözlenen context aralığından sonraki aynı 32 ardışık kaynak darbesini tahmin eder.' if boundary else 'Her context uzunluğu aynı son 32 hedef konumunu tahmin eder.')+' PRI birimi µs, frekans birimi MHz.',
          'Multivariate model beş giriş kanalı kullanır. Burada yalnızca PRI ve frekans MAE gösterilir.',
          'Her satırın en düşük MAE değeri kalındır; tam eşitliklerde tüm eşit değerler işaretlenir. Gösterim 6 ondalıktır.',
          f'Kaynak koşu: `{SOURCE.name}`. Kaynak metrik dosyası: `metrics.csv`.', '']
    pngs = OUT/'png'
    pngs.mkdir(exist_ok=True)
    for profile, mode, target, unit, rows in views:
        md.extend([f'## {profile.capitalize()} — {mode} — {target} MAE ({unit})', '',
                   '| Radar type | Error level | L=96 | L=256 | L=512 | L=992 |',
                   '|---|---|---:|---:|---:|---:|'])
        for radar, level, *values in rows:
            best = min(values)
            cells = [f'**{v:.6f}**' if v == best else f'{v:.6f}' for v in values]
            md.append('| ' + ' | '.join([radar, level, *cells]) + ' |')
        md.append('')
        name = f'{family}_{profile}_{mode.lower()}_{target.lower()}'
        with (OUT/f'{name}.csv').open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.writer(stream)
            writer.writerow(['radar_type', 'error_level', *[f'MAE_L{n}_{unit}' for n in CONTEXTS]])
            writer.writerows(rows)
        fig, ax = plt.subplots(figsize=(13.8, 20.8))
        ax.axis('off')
        fig.suptitle(f'Chronos-2 [{family}]: {profile}, {mode.lower()}, {target}',
                     fontsize=17, fontweight='bold', x=.04, ha='left', y=.99)
        ax.set_title(f'MAE ({unit})   H=32   200 test sequences per row   Green: lowest MAE in row',
                     fontsize=11, loc='left', pad=15)
        table = ax.table(cellText=[[r, e, *[f'{v:.6f}' for v in values]] for r, e, *values in rows],
                         colLabels=['Radar type', 'Error level', *[f'L={n}' for n in CONTEXTS]],
                         colWidths=[.24, .14, .155, .155, .155, .155],
                         cellLoc='right', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        for (i, j), cell in table.get_celld().items():
            cell.set_linewidth(.3)
            cell.set_edgecolor('#DCE2EA')
            if i == 0:
                cell.set_facecolor('#1C304D'); cell.set_text_props(color='white', weight='bold')
            else:
                values = rows[i-1][2:]
                cell.set_facecolor('#F1F5F9' if ((i-1)//8)%2 else 'white')
                if j < 2:
                    cell.set_text_props(ha='left')
                elif values[j-2] == min(values):
                    cell.set_facecolor('#DDEEDC'); cell.set_text_props(weight='bold', color='#174A26')
        fig.subplots_adjust(top=.95, bottom=.015, left=.04, right=.98)
        fig.savefig(pngs/f'{name}.png', dpi=140)
        plt.close(fig)
    (OUT/'MAE_comparison.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
    write_xlsx(profile_rows,family)
    assert digest(SOURCE/'metrics.csv') == original_hash
    audit = {'source_metrics_sha256': original_hash, 'source_conditions': len(source),
             'mae_values_checked_against_per_sequence_files': checked,
             'comparison_rows': sum(map(len, profile_rows.values())),
             'context_lengths': CONTEXTS, 'horizon': 32, 'test_sequences_per_condition': 200,
             'tables': len(views), 'source_unchanged': True,'protocol':protocol,
             'source_run':SOURCE.name,'window_mode':config['window_mode'],'dataset_family':family}
    (OUT/'validation.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(audit))


def write_xlsx(profile_rows,protocol):
    """Write the static comparison without requiring optional Excel packages."""
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def cell(ref, value, style):
        if isinstance(value, (int, float)):
            return f'<c r="{ref}" s="{style}"><v>{value!r}</v></c>'
        return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    def row(index, values, style=0, height=21):
        return f'<row r="{index}" ht="{height}" customHeight="1">'+''.join(
            cell(f'{chr(65+j)}{index}', v, 2 if isinstance(v, (int,float)) else style)
            for j, v in enumerate(values))+'</row>'
    styles = f'''<styleSheet xmlns="{ns}">
      <numFmts count="1"><numFmt numFmtId="164" formatCode="0.000000"/></numFmts>
      <fonts count="3"><font><sz val="11"/><name val="Arial"/><color rgb="FF172B4D"/></font><font><b/><sz val="11"/><name val="Arial"/><color rgb="FFFFFFFF"/></font><font><b/><sz val="15"/><name val="Arial"/><color rgb="FF172B4D"/></font></fonts>
      <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF1C304D"/><bgColor indexed="64"/></patternFill></fill></fills>
      <borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>
      <cellXfs count="4"><xf fontId="0" fillId="0" borderId="0" xfId="0"><alignment vertical="center"/></xf><xf fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf><xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"><alignment horizontal="right" vertical="center"/></xf><xf fontId="2" fillId="0" borderId="0" xfId="0"/></cellXfs>
      <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
      <dxfs count="1"><dxf><font><b/><color rgb="FF174A26"/></font><fill><patternFill patternType="solid"><fgColor rgb="FFDDEEDC"/><bgColor indexed="64"/></patternFill></fill></dxf></dxfs>
    </styleSheet>'''
    sheets = []
    for profile, rows in profile_rows.items():
        last = len(rows)+5
        body = row(2, [f'Chronos-2 zero-shot MAE: {profile} ({protocol})'], 3, 28)
        body += row(3, ['H=32. 200 test sequences per condition. L=96/256/512/992. Lowest MAE per row highlighted.'])
        body += row(5, HEADERS, 1, 25)
        body += ''.join(row(i, values) for i, values in enumerate(rows, 6))
        widths = [18, 16, 25, 17, 17, 17, 17, 17, 10]
        columns = ''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in enumerate(widths,1))
        sheets.append(f'''<worksheet xmlns="{ns}"><dimension ref="A1:I{last}"/>
          <sheetViews><sheetView workbookViewId="0" showGridLines="0"><pane xSplit="4" ySplit="5" topLeftCell="E6" activePane="bottomRight" state="frozen"/></sheetView></sheetViews>
          <sheetFormatPr defaultRowHeight="21"/><cols>{columns}</cols><sheetData>{body}</sheetData>
          <autoFilter ref="A5:I{last}"/>
          <conditionalFormatting sqref="E6:H{last}"><cfRule type="expression" dxfId="0" priority="1"><formula>E6=MIN($E6:$H6)</formula></cfRule></conditionalFormatting>
          <pageMargins left="0.3" right="0.3" top="0.4" bottom="0.4" header="0.2" footer="0.2"/>
        </worksheet>''')
    destination = OUT/f'{protocol}_chronos2_zero_shot_mae.xlsx'
    assert not destination.exists(), destination
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as book:
        content = ['<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
        content.extend(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in (1,2))
        book.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+''.join(content)+'</Types>')
        book.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        book.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Fixed" sheetId="1" r:id="rId1"/><sheet name="Varying" sheetId="2" r:id="rId2"/></sheets></workbook>')
        relationships = ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in (1,2))
        relationships += '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        book.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+relationships+'</Relationships>')
        book.writestr('xl/styles.xml', styles)
        for i, xml in enumerate(sheets, 1):
            book.writestr(f'xl/worksheets/sheet{i}.xml', xml)
    # Reopen every sheet and reconcile all 2048 numeric MAEs with the source-derived table.
    with zipfile.ZipFile(destination) as book:
        assert book.testzip() is None
        for i, expected in enumerate(profile_rows.values(), 1):
            sheet = ET.fromstring(book.read(f'xl/worksheets/sheet{i}.xml'))
            values = sheet.findall(f'{{{ns}}}sheetData/{{{ns}}}row')[3:]
            assert len(values) == len(expected)
            for xmlrow, record in zip(values, expected, strict=True):
                cells = xmlrow.findall(f'{{{ns}}}c')
                actual = [float(cells[j].find(f'{{{ns}}}v').text) for j in range(4,8)]
                assert actual == record[4:8]


if __name__ == '__main__':
    main()
