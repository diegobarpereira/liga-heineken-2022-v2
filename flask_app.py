import collections
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from flask import Flask, render_template, request
from matplotlib import pyplot as plt

import cartolafc.models
from cartolafc.constants import rodadas_campeonato, rodadas_primeiro_turno, rodadas_segundo_turno, \
    rodadas_liberta_prim_turno, grupo_liberta_prim_turno, rodadas_oitavas_prim_turno, list_oitavas_prim_turno, \
    rodadas_quartas_prim_turno, list_quartas_prim_turno, rodadas_semis_prim_turno, list_semis_prim_turno, \
    rodadas_finais_prim_turno, \
    list_finais_prim_turno, dict_prem, rodadas_liberta_seg_turno, grupo_liberta_seg_turno, rodadas_oitavas_seg_turno, \
    dict_matamata, rodadas_quartas_seg_turno, rodadas_semis_seg_turno, rodadas_finais_seg_turno

root_dir = os.path.dirname(os.path.abspath(__file__))

api = cartolafc.Api(
    glb_id='1b62a06f6d67add624e2360012d974b304a5044624c486a50716e5a374a666539744c3738702d386b79516e466c36466f546546585070585f4c414b74666a6f4273597363697258754b374a6d7257487a724b716c7a36653531556f555a6f6f2d503665574e673d3d3a303a646965676f2e323031312e382e35')

rod = api.mercado().rodada_atual
mercado_status = api.mercado().status.nome

app = Flask(__name__)
app.url_map.strict_slashes = False

times_ids = []
if api.mercado().status.nome != 'Mercado em manutenção':
    ligas = api.liga('liga-heineken-2022')

    for lig in ligas.times:
        times_ids.append(lig.ids)

todos_ids = [1241021, 1893918, 1245808, 8912058, 1889674, 13957925, 71375, 48733,
             3646412, 219929, 1235701, 25582672, 25588958, 315637, 18796615,
             19190102, 579336, 44514741, 44509672, 14439636, 279314, 28919430,
             19317259, 44558779, 977136]

rar = ['Peixão Irado', 'Christimao', 'Diego Pereira FC', 'Markitos Bar', '0VINTE1 FC',
       'oSantista', 'Denoris F.C.', 'Gabitreta F C', 'Camisa21FC',
       'Eae Malandro FC', 'JevyGoal', 'JUNA FUTEBOL CLUBE', 'Real Beach Soccer',
       'Golden Lions FC', 'ThiagoRolo FC', 'CFDS06', 'Rod Santos FC',
       'ArrascaMaisDez', 'AvantiHulkFc', 'Gonella Verde ', 'Xanpion']


@app.route('/')
def index_page():
    if api.mercado().status.nome == 'Mercado em manutenção':
        return render_template('manutencao.html')
    else:
        liga = api.liga('liga-heineken-2022')
        nome = liga.nome
        escudo = liga.escudo
        if mercado_status == 'Mercado Aberto' or mercado_status == 'Mercado fechado':
            return render_template('index.html', get_nome=nome, get_escudo=escudo)
        if mercado_status == 'Final de temporada':
            fim_de_temporada = 'A temporada de 2022 chegou ao fim.'
            return render_template('index.html', get_nome=nome, get_escudo=escudo, fim_de_temporada=fim_de_temporada)


@app.route('/participantes')
def participantes_page():
    liga = api.liga('liga-heineken-2022')
    nome = liga.nome
    escudo = liga.escudo
    return render_template('participantes.html', get_list=retornar_participantes(), get_escudo=escudo)


@app.route('/scouts')
def parciais_page():
    return render_template('scouts.html', get_list=parciais())


@app.route('/partidas')
def partidas_page():
    return render_template('partidas.html', rodada=rod, get_list=retornar_partidas())


@app.route('/pontuacoes')
def pontuacoes_page():
    pont_liga, list_max, media = pontos()

    return render_template('pontuacoes.html', get_list=pont_liga, get_max=list_max, get_media=media)


@app.route('/class')
def class_page():
    primeiro_turno, segundo_turno, campeonato, sem_capitao = liga_class()

    return render_template('class_2.html',
                           get_total=sorted(campeonato.items(), key=lambda v: v[1][1], reverse=True),
                           get_prim_turno=sorted(primeiro_turno.items(), key=lambda v: v[1][1], reverse=True),
                           get_seg_turno=sorted(segundo_turno.items(), key=lambda v: v[1][1], reverse=True),
                           get_semcapitao=sem_capitao.items(), key=lambda v: v[1][1], reverse=True)


@app.route('/stats')
def stats_page():
    return render_template('stats.html', get_list=retornar_estats_liga())


@app.route("/media", methods=['GET', 'POST'])
def get_media_form():
    dropdown_times = []

    for lig in ligas.times:
        dropdown_times.append(lig.nome)

    dropdown_times.sort()

    return render_template('media_form.html', dropdown_times=dropdown_times)


@app.route("/media_result", methods=['GET', 'POST'])
def return_media_form():
    team = request.form.get("time")
    gd = {}

    get_data = retornar_medias_time(team)
    for k, v in get_data.items():
        gd[k] = v

    root_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(root_dir, 'static/media.jpg')
    get_img = img_path

    return render_template('media_result.html', get_data=gd, get_time=team, get_img=get_img)


@app.route('/destaques')
def dest_page():
    return render_template('destaques.html', get_list=retornar_destaques(), get_capitaes=retornar_capitaes(),
                           get_reservas=retornar_reservas())


@app.route('/premiacao')
def premiacao_page():
    # lider_prim_turno, lider_seg_turno, prem, campeao_geral, vice_campeao, terc_colocado, quarto_colocado, campeao, vice = premiacao()
    # lider_prim_turno, prem, campeao, vice = premiacao()
    lider_prim_turno, lider_seg_turno, prem, campeao_prim_turno, vice_prim_turno, campeao_seg_turno, vice_seg_turno,\
        campeao_geral, vice_campeao, terc_colocado, quarto_colocado = premiacao()
    # print(lider_prim_turno)
    # print(prem)
    # print(campeao_prim_turno)
    # print(vice_prim_turno)

    return render_template('premiacao.html', lider_prim_turno=lider_prim_turno, lider_seg_turno=lider_seg_turno,
                           get_prem=prem,
                           campeao=campeao_prim_turno, vice=vice_prim_turno, campeao_seg_turno=campeao_seg_turno,
                           vice_seg_turno=vice_seg_turno, get_lider=campeao_geral, vice_campeao=vice_campeao,
                           terc_colocado=terc_colocado, quarto_colocado=quarto_colocado)


@app.route("/liberta")
def liberta_primeiro_turno():
    rod_6, rod_7, rod_8, rod_9, rod_10, rod_11, g1, g2, g3, g4, g5, g6 = get_liberta_prim_turno()
    g1_ = sorted(g1, key=lambda y: (y[4], y[5]), reverse=True)
    g2_ = sorted(g2, key=lambda y: (y[4], y[5]), reverse=True)
    g3_ = sorted(g3, key=lambda y: (y[4], y[5]), reverse=True)
    g4_ = sorted(g4, key=lambda y: (y[4], y[5]), reverse=True)
    g5_ = sorted(g5, key=lambda y: (y[4], y[5]), reverse=True)
    g6_ = sorted(g6, key=lambda y: (y[4], y[5]), reverse=True)
    liga = api.liga('liga-heineken-2022')
    escudo = liga.escudo
    return render_template('liberta.html', get_escudo=escudo, get_list=rod_6, get_list2=rod_7,
                           get_list3=rod_8, get_list4=rod_9, get_list5=rod_10, get_list6=rod_11,
                           data1=g1_, data2=g2_, data3=g3_, data4=g4_, data5=g5_, data6=g6_
                           )


@app.route('/matamataprimturno')
def matamata_page():
    oit_a, oit_b, qua_a, qua_b, semi_a, semi_b, final_a, final_b, esq_maior = mata_mata_prim_turno()
    final = True

    campeao = []
    vice = []

    for f_a, f_b in zip(final_a, final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao = [[f_a[1], f_a[2]]]
            vice = [[f_b[1], f_b[2]]]
        else:
            campeao = [[f_b[1], f_b[2]]]
            vice = [[f_a[1], f_a[2]]]

    return render_template('matamata.html', get_list1=oit_a, get_list2=oit_b, get_list3=qua_a,
                           get_list4=qua_b, get_list5=semi_a, get_list6=semi_b, get_list7=final_a,
                           get_list8=final_b, esq_maior=esq_maior, campeao=campeao, vice=vice, final=final)


@app.route("/liberta2")
def liberta_segundo_turno():
    rod_6, rod_7, rod_8, rod_9, rod_10, rod_11, g1, g2, g3, g4, g5, g6 = get_liberta_seg_turno()
    g1_ = sorted(g1, key=lambda y: (y[4], y[5]), reverse=True)
    g2_ = sorted(g2, key=lambda y: (y[4], y[5]), reverse=True)
    g3_ = sorted(g3, key=lambda y: (y[4], y[5]), reverse=True)
    g4_ = sorted(g4, key=lambda y: (y[4], y[5]), reverse=True)
    g5_ = sorted(g5, key=lambda y: (y[4], y[5]), reverse=True)
    g6_ = sorted(g6, key=lambda y: (y[4], y[5]), reverse=True)
    liga = api.liga('liga-heineken-2022')
    escudo = liga.escudo
    return render_template('liberta2.html', get_escudo=escudo, get_list=rod_6, get_list2=rod_7,
                           get_list3=rod_8, get_list4=rod_9, get_list5=rod_10, get_list6=rod_11,
                           data1=g1_, data2=g2_, data3=g3_, data4=g4_, data5=g5_, data6=g6_
                           )


@app.route('/matamatasegturno')
def matamata_seg_page():
    # oit_a, oit_b, qua_a, qua_b, semi_a, semi_b, final_a, final_b, esq_maior = mata_mata_prim_turno()
    oit_a, oit_b, qua_a, qua_b, semi_a, semi_b, final_a, final_b, esq_maior = mata_mata_seg_turno()
    final = True

    campeao = []
    vice = []

    for f_a, f_b in zip(final_a, final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao = [[f_a[1], f_a[2]]]
            vice = [[f_b[1], f_b[2]]]
        else:
            campeao = [[f_b[1], f_b[2]]]
            vice = [[f_a[1], f_a[2]]]

    # , get_list3 = qua_a,
    # get_list4 = qua_b, get_list5 = semi_a, get_list6 = semi_b, get_list7 = final_a,
    # get_list8 = final_b, esq_maior = esq_maior, campeao = campeao, vice = vice, final = final
    return render_template('matamata_seg_turno.html', get_list1=oit_a, get_list2=oit_b, get_list3=qua_a,
                           get_list4=qua_b, get_list5=semi_a, get_list6=semi_b, get_list7=final_a, get_list8=final_b,
                           esq_maior=esq_maior, campeao=campeao, vice=vice, final=final)


def get_times_campeonato():
    liga_class = api.liga('liga-heineken-2022')
    return liga_class


def retornar_participantes():
    dict_participantes = {}
    with open('static/participantes.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_participantes[k] = v

    return dict_participantes


def parciais():
    scout = {'G': 0, 'A': 0, 'FT': 0, 'FD': 0, 'FF': 0, 'FS': 0, 'PS': 0, 'DS': 0, 'SG': 0,
             'DE': 0, 'DP': 0, 'PI': 0, 'I': 0, 'PP': 0, 'PC': 0, 'FC': 0, 'CA': 0, 'CV': 0,
             'GC': 0, 'GS': 0}
    list_parciais = []

    if api.mercado().status.nome == 'Mercado fechado':
        get_parciais = api.parciais()
        parciais_sorted = sorted(get_parciais.values(), key=lambda pts: pts.pontos, reverse=True)

        for chave in parciais_sorted:
            list_parciais.append([chave.foto, chave.apelido, chave.clube.escudos, chave.posicao.abreviacao,
                                  {key: chave.scout[key] for key in scout.keys() if key in chave.scout},
                                  "{:.2f}".format(chave.pontos)])
    else:
        get_parciais = api.parciais(rod - 1)
        parciais_sorted = sorted(get_parciais.values(), key=lambda pts: pts.pontos, reverse=True)

        for chave in parciais_sorted:
            list_parciais.append([chave.foto, chave.apelido, chave.clube.escudos, chave.posicao.abreviacao,
                                  {key: chave.scout[key] for key in scout.keys() if key in chave.scout},
                                  "{:.2f}".format(chave.pontos)])

    return list_parciais


def retornar_partidas():
    rodada = api.mercado().rodada_atual
    partidas = api.partidas(rodada)

    dict_partidas = {}

    for partida in partidas:
        if partida.valida:

            if partida.clube_casa.nome in dict_partidas or partida.clube_visitante.nome in dict_partidas:
                dict_partidas[partida.clube_casa.nome] = {
                    'Data': partida.data.strftime('%d-%m-%Y %H:%M'),
                    'Local': partida.local,
                    'Escudo_Casa': partida.clube_casa_escudo.escudos,
                    'Casa_Posicao': str(partida.clube_casa_posicao) + 'º',
                    'Clube_Casa': partida.clube_casa.nome,
                    'Placar_Casa': partida.placar_casa if partida.placar_casa else 0,
                    'X': 'x',
                    'Placar_Visitante': partida.placar_visitante if partida.placar_visitante else 0,
                    'Clube_Visitante': partida.clube_visitante.nome,
                    'Visitante_Posicao': str(partida.clube_visitante_posicao) + 'º',
                    'Escudo_Visitante': partida.clube_visitante_escudo.escudos
                }
            else:
                dict_partidas[partida.clube_casa.nome] = {
                    'Data': partida.data.strftime('%d-%m-%Y %H:%M'),
                    'Local': partida.local,
                    'Escudo_Casa': partida.clube_casa_escudo.escudos,
                    'Casa_Posicao': str(partida.clube_casa_posicao) + 'º',
                    'Clube_Casa': partida.clube_casa.nome,
                    'Placar_Casa': partida.placar_casa if partida.placar_casa else 0,
                    'X': 'x',
                    'Placar_Visitante': partida.placar_visitante if partida.placar_visitante else 0,
                    'Clube_Visitante': partida.clube_visitante.nome,
                    'Visitante_Posicao': str(partida.clube_visitante_posicao) + 'º',
                    'Escudo_Visitante': partida.clube_visitante_escudo.escudos
                }

        else:
            if partida.clube_casa.nome in dict_partidas or partida.clube_visitante.nome in dict_partidas:
                dict_partidas[partida.clube_casa.nome] = {
                    'Data': 'Partida não é',
                    'Local': 'valida para a rodada',
                    'Escudo_Casa': partida.clube_casa_escudo.escudos,
                    'Casa_Posicao': str(partida.clube_casa_posicao) + 'º',
                    'Clube_Casa': partida.clube_casa.nome,
                    'Placar_Casa': partida.placar_casa if partida.placar_casa else 0,
                    'X': 'x',
                    'Placar_Visitante': partida.placar_visitante if partida.placar_visitante else 0,
                    'Clube_Visitante': partida.clube_visitante.nome,
                    'Visitante_Posicao': str(partida.clube_visitante_posicao) + 'º',
                    'Escudo_Visitante': partida.clube_visitante_escudo.escudos
                }
            else:
                dict_partidas[partida.clube_casa.nome] = {
                    'Data': 'Partida não é',
                    'Local': 'valida para a rodada',
                    'Escudo_Casa': partida.clube_casa_escudo.escudos,
                    'Casa_Posicao': str(partida.clube_casa_posicao) + 'º',
                    'Clube_Casa': partida.clube_casa.nome,
                    'Placar_Casa': partida.placar_casa if partida.placar_casa else 0,
                    'X': 'x',
                    'Placar_Visitante': partida.placar_visitante if partida.placar_visitante else 0,
                    'Clube_Visitante': partida.clube_visitante.nome,
                    'Visitante_Posicao': str(partida.clube_visitante_posicao) + 'º',
                    'Escudo_Visitante': partida.clube_visitante_escudo.escudos
                }

    return dict_partidas


def pontos():
    dict_time = {}
    dict_nome = {}
    dict_temp_pontos = {}
    dict_nome_escudo_pontos = {}
    dict_pontos = {}
    dict_parciais = {}
    media = []
    max_val = []

    with open('static/times_rodada.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for camp in rodadas_campeonato:
        for key, value in dict_time.items():
            if key == str(camp):
                for v in value.items():
                    if v[0] in dict_temp_pontos:
                        dict_temp_pontos[v[0]].append(v[1])
                    else:
                        dict_temp_pontos[v[0]] = [v[1]]

    for chave, valor in dict_temp_pontos.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_nome_escudo_pontos[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado' and rod > 1:
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, todos_ids)

        for teams in threads:
            dict_parciais[teams.info.nome] = teams.pontos

        for c, v in dict_parciais.items():
            for chave, valor in dict_nome_escudo_pontos.items():
                if c == chave:
                    valor[1].append(v)

    ordenar_dict = sorted(dict_nome_escudo_pontos.items(), key=lambda t: sum(t[1][1]), reverse=True)
    for k in ordenar_dict:
        dict_pontos[k[0]] = k[1]

    if api.mercado().status.nome == 'Mercado aberto':

        for x in range(0, rod - 1):
            res = 0.00
            res_ = 0.00
            for k, v in dict_temp_pontos.items():
                res += v[x]
            res_ = res / len(dict_temp_pontos.keys())
            media.append(res_)

        list_to_delete = ['Raça Timão!!!', 'FAFA SHOW FC', 'Sóh Taapa FC', 'RIVA 77 ']

        for ltd in list_to_delete:
            for id, nome in json.loads(nomes).items():
                if ltd == nome:
                    dict_temp_pontos.pop(id)

        for chave, valor in dict_temp_pontos.items():
            for id, nome in json.loads(nomes).items():
                if chave == id:
                    dict_nome[nome] = valor

        for x in range(0, api.mercado().rodada_atual - 1):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_nome.items()}.items(), key=lambda y: y[1],
                                     reverse=True)

            if max_cada_rodada[0][0] in rar:
                if max_cada_rodada[0][1] == max_cada_rodada[1][1]:
                    max_val.append(f'{max_cada_rodada[0][0]} / {max_cada_rodada[1][0]}')
                else:
                    max_val.append(max_cada_rodada[0][0])

    if api.mercado().status.nome == 'Mercado fechado':

        for x in range(0, rod):
            res = 0.00
            res_ = 0.00
            for k, v in dict_temp_pontos.items():
                res += v[x]
            res_ = res / len(dict_temp_pontos.keys())
            media.append(res_)

        list_to_delete = ['Raça Timão!!!', 'FAFA SHOW FC', 'Sóh Taapa FC', 'RIVA 77 ']

        for ltd in list_to_delete:
            for id, nome in json.loads(nomes).items():
                if ltd == nome:
                    dict_temp_pontos.pop(id)

        for chave, valor in dict_temp_pontos.items():
            for id, nome in json.loads(nomes).items():
                if chave == id:
                    dict_nome[nome] = valor

        for x in range(0, api.mercado().rodada_atual):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_nome.items()}.items(), key=lambda y: y[1],
                                     reverse=True)

            if max_cada_rodada[0][0] in rar:
                if max_cada_rodada[0][1] == max_cada_rodada[1][1]:
                    max_val.append(f'{max_cada_rodada[0][0]} / {max_cada_rodada[1][0]}')
                else:
                    max_val.append(max_cada_rodada[0][0])

    if api.mercado().status.nome == 'Final de temporada':
        list_to_delete = ['Raça Timão!!!', 'FAFA SHOW FC', 'Sóh Taapa FC', 'RIVA 77 ']

        for ltd in list_to_delete:
            for id, nome in json.loads(nomes).items():
                if ltd == nome:
                    dict_temp_pontos.pop(id)

        for chave, valor in dict_temp_pontos.items():
            for id, nome in json.loads(nomes).items():
                if chave == id:
                    dict_nome[nome] = valor

        for x in range(0, api.mercado().rodada_atual):
            max_cada_rodada = sorted({k: v[x] for k, v in dict_nome.items()}.items(), key=lambda y: y[1],
                                     reverse=True)
            if max_cada_rodada[0][0] in rar:
                if max_cada_rodada[0][1] == max_cada_rodada[1][1]:
                    max_val.append(f'{max_cada_rodada[0][0]} / {max_cada_rodada[1][0]}')
                else:
                    max_val.append(max_cada_rodada[0][0])

    return dict_pontos, max_val, media


def liga_class():
    dict_prim_turno = {}
    dict_prim_turno_pts = {}
    primeiro_turno_ = {}
    primeiro_turno = {}
    dict_seg_turno = {}
    dict_seg_turno_pts = {}
    segundo_turno_ = {}
    segundo_turno = {}
    dict_campeonato = {}
    dict_campeonato_pts = {}
    campeonato_ = {}
    campeonato = {}
    dict_sem_capitao = {}
    sem_capitao = {}
    threads = []
    teams = []
    team_dict = {}
    dict_times_rodadas = {}

    with open('static/times_rodada.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for prim_turno in rodadas_primeiro_turno:
        for key, value in json.loads(data).items():
            if key == str(prim_turno):
                for v in value.items():
                    if v[0] in dict_prim_turno:
                        dict_prim_turno[v[0]].append(v[1])
                    else:
                        dict_prim_turno[v[0]] = [v[1]]

    ordenar_dict = sorted(dict_prim_turno.items(), key=lambda t: sum(t[1]), reverse=True)
    for k in ordenar_dict:
        primeiro_turno_[k[0]] = sum(k[1])

    for seg_turno in rodadas_segundo_turno:
        for key, value in json.loads(data).items():
            if key == str(seg_turno):
                for v in value.items():
                    if v[0] in dict_seg_turno:
                        dict_seg_turno[v[0]].append(v[1])
                    else:
                        dict_seg_turno[v[0]] = [v[1]]

    ordenar_dict = sorted(dict_seg_turno.items(), key=lambda t: sum(t[1]), reverse=True)
    for k_ in ordenar_dict:
        segundo_turno_[k_[0]] = sum(k_[1])

    for camp in rodadas_campeonato:
        for key, value in json.loads(data).items():
            if key == str(camp):
                for v in value.items():
                    if v[0] in dict_campeonato:
                        dict_campeonato[v[0]].append(v[1])
                    else:
                        dict_campeonato[v[0]] = [v[1]]

    ordenar_dict = sorted(dict_campeonato.items(), key=lambda t: sum(t[1]), reverse=True)
    for k__ in ordenar_dict:
        campeonato_[k__[0]] = sum(k__[1])

    with open('static/sem_capitao.json', encoding='utf-8', mode='r') as currentFile:
        data_sem_capitao = currentFile.read().replace('\n', '')

        for x, y in json.loads(data_sem_capitao).items():
            dict_sem_capitao[x] = y

    if api.mercado().status.nome == 'Mercado aberto' or api.mercado().status.nome == 'Final de temporada':

        for (c1, v1), (chave, valor), (chave_, valor_), (chave_sc, valor_sc) in zip(primeiro_turno_.items(),
                                                                                    campeonato_.items(),
                                                                                    segundo_turno_.items(),
                                                                                    dict_sem_capitao.items()):
            for c, e in json.loads(escudos).items():
                for k, n in json.loads(nomes).items():
                    if chave_ == c:
                        if chave_ == k:
                            segundo_turno[n] = [e, valor_]
                    if chave == c:
                        if chave == k:
                            campeonato[n] = [e, valor]
                    if chave_sc == c:
                        if chave_sc == k:
                            sem_capitao[n] = [e, valor_sc]
                    if c1 == c:
                        if c1 == k:
                            primeiro_turno[n] = [e, v1]

        data_times_rodadas = dict(json.loads(data).items())
        pen_rod = list(data_times_rodadas.keys())[-1]

        for key_, value_ in segundo_turno_.items():
            for key2_, value2_ in data_times_rodadas[pen_rod].items():
                if key_ == key2_:
                    for k2, n2 in json.loads(nomes).items():
                        if k2 == key_:
                            segundo_turno[n2].append(data_times_rodadas[pen_rod][key_])

        for key_, value_ in campeonato_.items():
            for key2_, value2_ in data_times_rodadas[pen_rod].items():
                if key_ == key2_:
                    for k2, n2 in json.loads(nomes).items():
                        if k2 == key_:
                            campeonato[n2].append(data_times_rodadas[pen_rod][key_])

    if api.mercado().status.nome == 'Mercado fechado':

        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, todos_ids)

            for teams in threads:
                team_dict[teams.info.id] = teams.pontos

            for (c1, v1), (chave, valor), (chave_, valor_), (chave_sc, valor_sc) in zip(primeiro_turno_.items(),
                                                                                        campeonato_.items(),
                                                                                        segundo_turno_.items(),
                                                                                        dict_sem_capitao.items()):
                for c, e in json.loads(escudos).items():
                    for k, n in json.loads(nomes).items():
                        for key, value in team_dict.items():
                            if chave_ == c:
                                if chave_ == k:
                                    if chave_ == str(key):
                                        segundo_turno[n] = [e, valor_ + value, value]
                            if chave == c:
                                if chave == k:
                                    if chave == str(key):
                                        campeonato[n] = [e, valor + value, value]
                            if chave_sc == c:
                                if chave_sc == k:
                                    sem_capitao[n] = [e, valor_sc]
                            if c1 == c:
                                if c1 == k:
                                    primeiro_turno[n] = [e, v1]

    primeiro_turno.pop('AvantiHulkFc')
    segundo_turno.pop('AvantiHulkFc')
    campeonato.pop('AvantiHulkFc')

    lider_prim_turno = next(iter(primeiro_turno))
    lider_seg_turno = next(iter(segundo_turno))

    dict_prem['primeiro_turno']['lider'] = lider_prim_turno
    dict_prem['segundo_turno']['lider'] = lider_seg_turno

    with open(f'static/dict_prem.json', 'w', encoding='utf-8') as f:
        json.dump(dict_prem, f)

    return primeiro_turno, segundo_turno, campeonato, sem_capitao


def retornar_estats_liga():
    dict_time_stats = {}

    with open('static/times_stats.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time_stats[k] = v

    return dict_time_stats


def times_rodadas(id_, rodada):
    if mercado_status == 'Mercado aberto':
        if rodada < rod:
            time_ = api.time(id_, rodada=rodada)
        else:
            time_ = api.time_parcial(id_)

    if mercado_status == 'Final de temporada':
        time_ = api.time(id_, rodada=rodada)

    return time_


def retornar_media_time_rodada(id_):
    threads = []
    teams = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        if mercado_status == 'Mercado aberto':
            for x in range(1, rod):
                threads.append(executor.submit(times_rodadas, id_, rodada=x))

        if mercado_status == 'Final de temporada':
            for x in range(1, rod + 1):
                threads.append(executor.submit(times_rodadas, id_, rodada=x))

        for task in as_completed(threads):
            teams.append(task.result())

    return teams


def retornar_medias_time(cartola_time: str):
    dict_medias = {}
    gol = 0
    somagol = 0
    lat = 0
    somalat = 0
    zag = 0
    somazag = 0
    meia = 0
    somameia = 0
    ata = 0
    somaata = 0
    tec = 0
    somatec = 0
    time_id = 0

    for part in ligas.times:
        if cartola_time in part.nome:
            time_id = part.id
            break

    media_total = api.time(time_id)
    if mercado_status == 'Mercado aberto':
        mt = "{:.2f}".format(media_total.pontos / (rod - 1))
    if mercado_status == 'Final de temporada':
        mt = "{:.2f}".format(media_total.pontos / (rod))

    for t in retornar_media_time_rodada(time_id):
        for value in t.atletas:

            if value.posicao.nome == 'Goleiro':
                gol = gol + 1
                somagol = somagol + value.pontos
            elif value.posicao.nome == 'Lateral':
                lat = lat + 1
                somalat = somalat + value.pontos
            elif value.posicao.nome == 'Zagueiro':
                zag = zag + 1
                somazag = somazag + value.pontos
            elif value.posicao.nome == 'Meia':
                meia = meia + 1
                somameia = somameia + value.pontos
            elif value.posicao.nome == 'Atacante':
                ata = ata + 1
                somaata = somaata + value.pontos
            elif value.posicao.nome == 'Técnico':
                tec = tec + 1
                somatec = somatec + value.pontos
            else:
                pass

        dict_medias[t.info.nome, mt] = [somagol / gol, (somalat / lat) if somalat or lat else 0, somazag / zag,
                                        somameia / meia, somaata / ata, somatec / tec]

    for x_axis in dict_medias.values():
        left = [1, 2, 3, 4, 5, 6]
        x = ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA', 'TEC']
        y = [x_axis[0], x_axis[1], x_axis[2], x_axis[3], x_axis[4], x_axis[5]]
        # plt.bar(left, y, tick_label=x,
        #         width=0.8, color=['red', 'green'])

        z = np.arange(len(x))  # the label locations
        width = 0.8  # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(z, y, width, label='Média')

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_xticks(z)
        ax.set_xticklabels(x)
        ax.legend()

        ax.bar_label(rects1, padding=3)

        fig.tight_layout()
        plt.savefig('static/media.jpg', dpi=400)
        # plt.show()

    return dict_medias


def retornar_destaques():
    with open('static/partidas.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    dict_time = json.loads(data)

    destaques = api.destaques()
    atletas = api.mercado_atletas()

    list_destaques = []
    for destaque in destaques:
        list_destaques.append(destaque)

        for partida in dict_time:

            if partida['valida']:

                if destaque.clube_nome == partida['clube_casa']['nome']:
                    destaque.mand = True
                    destaque.adv = partida["clube_visitante"]["escudos"]

                if destaque.clube_nome == partida['clube_visitante']['nome']:
                    destaque.mand = False
                    destaque.adv = partida["clube_casa"]["escudos"]

        for at in atletas:
            if destaque.atleta['atleta_id'] == at.id:
                destaque.minimo_para_valorizar = at.minimo_para_valorizar

    return list_destaques


def retornar_capitaes():
    with open('static/partidas.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    dict_time = json.loads(data)

    capitaes = api.capitaes()
    atletas = api.mercado_atletas()

    list_capitaes = []
    for capitao in capitaes:

        list_capitaes.append(capitao)

        for partida in dict_time:

            if capitao.clube_id == partida['clube_casa']['id']:
                capitao.mand = True
                capitao.clube_nome = partida['clube_casa']['escudos']
            if capitao.clube_id == partida['clube_visitante']['id']:
                capitao.mand = False
                capitao.clube_nome = partida['clube_visitante']['escudos']

            if partida['valida']:

                if capitao.clube_id == partida['clube_casa']['id']:
                    capitao.mand = True
                    capitao.adv = partida["clube_visitante"]["escudos"]

                if capitao.clube_id == partida['clube_visitante']['id']:
                    capitao.mand = False
                    capitao.adv = partida["clube_casa"]["escudos"]

        for at in atletas:
            if capitao.atleta['atleta_id'] == at.id:
                capitao.minimo_para_valorizar = at.minimo_para_valorizar

    return list_capitaes


def retornar_reservas():
    with open('static/partidas.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    dict_time = json.loads(data)

    reservas = api.reservas()
    atletas = api.mercado_atletas()

    list_reservas = []
    for reserva in reservas:

        list_reservas.append(reserva)

        for partida in dict_time:

            if reserva.clube_id == partida['clube_casa']['id']:
                reserva.mand = True
                reserva.clube_nome = partida['clube_casa']['escudos']
            if reserva.clube_id == partida['clube_visitante']['id']:
                reserva.mand = False
                reserva.clube_nome = partida['clube_visitante']['escudos']

            if partida['valida']:

                if reserva.clube_id == partida['clube_casa']['id']:
                    reserva.mand = True
                    reserva.adv = partida["clube_visitante"]["escudos"]

                if reserva.clube_id == partida['clube_visitante']['id']:
                    reserva.mand = False
                    reserva.adv = partida["clube_casa"]["escudos"]

        for at in atletas:
            if reserva.atleta['atleta_id'] == at.id:
                reserva.minimo_para_valorizar = at.minimo_para_valorizar

    return list_reservas


def premiacao():
    with open('static/dict_prem.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

    dict_pontos, max_val, media = pontos()

    lider_prim_turno = json.loads(data)['primeiro_turno']['lider']
    lider_seg_turno = json.loads(data)['segundo_turno']['lider']
    campeao_prim_turno = json.loads(data)['liberta_prim_turno']['campeao']
    vice_prim_turno = json.loads(data)['liberta_prim_turno']['vice']
    campeao_seg_turno = json.loads(data)['liberta_seg_turno']['campeao']
    vice_seg_turno = json.loads(data)['liberta_seg_turno']['vice']

    campeao_geral = next(iter(dict_pontos))
    vice_campeao = list(dict_pontos.keys())[1]
    terc_colocado = list(dict_pontos.keys())[2]
    quarto_colocado = list(dict_pontos.keys())[3]

    dict_rar_ = {}
    for time in rar:
        dict_rar_[time] = {'qtde': 0, 'valor': 0.00}

    for ganhador in max_val:

        if not "/" in ganhador:
            dict_rar_[ganhador]['qtde'] += 1
            dict_rar_[ganhador]['valor'] += float("{:.2f}".format(len(rar) * 1 * 2))
        else:
            dividido = ganhador.split(" / ")
            for r in dividido:
                dict_rar_[r]['qtde'] += 1
                dict_rar_[r]['valor'] += float("{:.2f}".format(len(rar) * 1 * 1))

    return lider_prim_turno, lider_seg_turno, dict_rar_, campeao_prim_turno, vice_prim_turno, campeao_seg_turno, \
           vice_seg_turno, campeao_geral, vice_campeao, terc_colocado,quarto_colocado


def get_times_rodada():
    dict_time = {}
    with open('static/times_rodada.json', encoding='utf-8', mode='r') as currentFile:
        data = currentFile.read().replace('\n', '')

        for k, v in json.loads(data).items():
            dict_time[k] = v

    return dict_time


def get_liberta_prim_turno():
    dict_liberta_ = collections.defaultdict(list)
    dict_liberta_pts = {}
    ordered_dict_liberta = {}

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_liberta_prim_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_liberta_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_liberta_[key].append(0.00)

    novo_dict_liberta = dict(dict_liberta_)

    for time_id in list(novo_dict_liberta):
        if int(time_id) not in grupo_liberta_prim_turno:
            novo_dict_liberta.pop(str(time_id))

    for item in grupo_liberta_prim_turno:
        ordered_dict_liberta[str(item)] = novo_dict_liberta[str(item)]

    for chave, valor in ordered_dict_liberta.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_liberta_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, grupo_liberta_prim_turno)

        for teams in threads:
            dict_liberta_pts[teams.info.nome].append(teams.pontos)

    rodada_6 = []
    rodada_7 = []
    rodada_8 = []
    rodada_9 = []
    rodada_10 = []
    rodada_11 = []
    jogos_rodada_6 = []
    jogos_rodada_7 = []
    jogos_rodada_8 = []
    jogos_rodada_9 = []
    jogos_rodada_10 = []
    jogos_rodada_11 = []

    for key, value in dict_liberta_pts.items():
        rodada_6.append([key, value[1][0]])
        rodada_7.append([key, value[1][1]])
        rodada_8.append([key, value[1][2]])
        rodada_9.append([key, value[1][3]])
        rodada_10.append([key, value[1][4]])
        rodada_11.append([key, value[1][5]])

    jogos_rodada_6.append([rodada_6[0][0], rodada_6[0][1], 'x', rodada_6[1][1], rodada_6[1][0]])
    jogos_rodada_6.append([rodada_6[2][0], rodada_6[2][1], 'x', rodada_6[3][1], rodada_6[3][0]])
    jogos_rodada_6.append([rodada_6[4][0], rodada_6[4][1], 'x', rodada_6[5][1], rodada_6[5][0]])
    jogos_rodada_6.append([rodada_6[6][0], rodada_6[6][1], 'x', rodada_6[7][1], rodada_6[7][0]])
    jogos_rodada_6.append([rodada_6[8][0], rodada_6[8][1], 'x', rodada_6[9][1], rodada_6[9][0]])
    jogos_rodada_6.append([rodada_6[10][0], rodada_6[10][1], 'x', rodada_6[11][1], rodada_6[11][0]])
    jogos_rodada_6.append([rodada_6[12][0], rodada_6[12][1], 'x', rodada_6[13][1], rodada_6[13][0]])
    jogos_rodada_6.append([rodada_6[14][0], rodada_6[14][1], 'x', rodada_6[15][1], rodada_6[15][0]])
    jogos_rodada_6.append([rodada_6[16][0], rodada_6[16][1], 'x', rodada_6[17][1], rodada_6[17][0]])
    jogos_rodada_6.append([rodada_6[18][0], rodada_6[18][1], 'x', rodada_6[19][1], rodada_6[19][0]])
    jogos_rodada_6.append([rodada_6[20][0], rodada_6[20][1], 'x', rodada_6[21][1], rodada_6[21][0]])
    jogos_rodada_6.append([rodada_6[22][0], rodada_6[22][1], 'x', rodada_6[23][1], rodada_6[23][0]])

    empate = False
    for x in jogos_rodada_6:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_7.append([rodada_7[0][0], rodada_7[0][1], 'x', rodada_7[2][1], rodada_7[2][0]])
    jogos_rodada_7.append([rodada_7[1][0], rodada_7[1][1], 'x', rodada_7[3][1], rodada_7[3][0]])

    jogos_rodada_7.append([rodada_7[4][0], rodada_7[4][1], 'x', rodada_7[6][1], rodada_7[6][0]])
    jogos_rodada_7.append([rodada_7[5][0], rodada_7[5][1], 'x', rodada_7[7][1], rodada_7[7][0]])

    jogos_rodada_7.append([rodada_7[8][0], rodada_7[8][1], 'x', rodada_7[10][1], rodada_7[10][0]])
    jogos_rodada_7.append([rodada_7[9][0], rodada_7[9][1], 'x', rodada_7[11][1], rodada_7[11][0]])

    jogos_rodada_7.append([rodada_7[12][0], rodada_7[12][1], 'x', rodada_7[14][1], rodada_7[14][0]])
    jogos_rodada_7.append([rodada_7[13][0], rodada_7[13][1], 'x', rodada_7[15][1], rodada_7[15][0]])

    jogos_rodada_7.append([rodada_7[16][0], rodada_7[16][1], 'x', rodada_7[18][1], rodada_7[18][0]])
    jogos_rodada_7.append([rodada_7[17][0], rodada_7[17][1], 'x', rodada_7[19][1], rodada_7[19][0]])

    jogos_rodada_7.append([rodada_7[20][0], rodada_7[20][1], 'x', rodada_7[22][1], rodada_7[22][0]])
    jogos_rodada_7.append([rodada_7[21][0], rodada_7[21][1], 'x', rodada_7[23][1], rodada_7[23][0]])

    empate = False
    for x in jogos_rodada_7:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_8.append([rodada_8[0][0], rodada_8[0][1], 'x', rodada_8[3][1], rodada_8[3][0]])
    jogos_rodada_8.append([rodada_8[1][0], rodada_8[1][1], 'x', rodada_8[2][1], rodada_8[2][0]])

    jogos_rodada_8.append([rodada_8[4][0], rodada_8[4][1], 'x', rodada_8[7][1], rodada_8[7][0]])
    jogos_rodada_8.append([rodada_8[5][0], rodada_8[5][1], 'x', rodada_8[6][1], rodada_8[6][0]])

    jogos_rodada_8.append([rodada_8[8][0], rodada_8[8][1], 'x', rodada_8[11][1], rodada_8[11][0]])
    jogos_rodada_8.append([rodada_8[9][0], rodada_8[9][1], 'x', rodada_8[10][1], rodada_8[10][0]])

    jogos_rodada_8.append([rodada_8[12][0], rodada_8[12][1], 'x', rodada_8[15][1], rodada_8[15][0]])
    jogos_rodada_8.append([rodada_8[13][0], rodada_8[13][1], 'x', rodada_8[14][1], rodada_8[14][0]])

    jogos_rodada_8.append([rodada_8[16][0], rodada_8[16][1], 'x', rodada_8[19][1], rodada_8[19][0]])
    jogos_rodada_8.append([rodada_8[17][0], rodada_8[17][1], 'x', rodada_8[18][1], rodada_8[18][0]])

    jogos_rodada_8.append([rodada_8[20][0], rodada_8[20][1], 'x', rodada_8[23][1], rodada_8[23][0]])
    jogos_rodada_8.append([rodada_8[21][0], rodada_8[21][1], 'x', rodada_8[22][1], rodada_8[22][0]])

    for x in jogos_rodada_8:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_9.append([rodada_9[1][0], rodada_9[1][1], 'x', rodada_9[0][1], rodada_9[0][0]])
    jogos_rodada_9.append([rodada_9[3][0], rodada_9[3][1], 'x', rodada_9[2][1], rodada_9[2][0]])

    jogos_rodada_9.append([rodada_9[5][0], rodada_9[5][1], 'x', rodada_9[4][1], rodada_9[4][0]])
    jogos_rodada_9.append([rodada_9[7][0], rodada_9[7][1], 'x', rodada_9[6][1], rodada_9[6][0]])

    jogos_rodada_9.append([rodada_9[9][0], rodada_9[9][1], 'x', rodada_9[8][1], rodada_9[8][0]])
    jogos_rodada_9.append([rodada_9[11][0], rodada_9[11][1], 'x', rodada_9[10][1], rodada_9[10][0]])

    jogos_rodada_9.append([rodada_9[13][0], rodada_9[13][1], 'x', rodada_9[12][1], rodada_9[12][0]])
    jogos_rodada_9.append([rodada_9[15][0], rodada_9[15][1], 'x', rodada_9[14][1], rodada_9[14][0]])

    jogos_rodada_9.append([rodada_9[17][0], rodada_9[17][1], 'x', rodada_9[16][1], rodada_9[16][0]])
    jogos_rodada_9.append([rodada_9[19][0], rodada_9[19][1], 'x', rodada_9[18][1], rodada_9[18][0]])

    jogos_rodada_9.append([rodada_9[21][0], rodada_9[21][1], 'x', rodada_9[20][1], rodada_9[20][0]])
    jogos_rodada_9.append([rodada_9[23][0], rodada_9[23][1], 'x', rodada_9[22][1], rodada_9[22][0]])

    for x in jogos_rodada_9:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_10.append([rodada_10[2][0], rodada_10[2][1], 'x', rodada_10[0][1], rodada_10[0][0]])
    jogos_rodada_10.append([rodada_10[3][0], rodada_10[3][1], 'x', rodada_10[1][1], rodada_10[1][0]])

    jogos_rodada_10.append([rodada_10[6][0], rodada_10[6][1], 'x', rodada_10[4][1], rodada_10[4][0]])
    jogos_rodada_10.append([rodada_10[7][0], rodada_10[7][1], 'x', rodada_10[5][1], rodada_10[5][0]])

    jogos_rodada_10.append([rodada_10[10][0], rodada_10[10][1], 'x', rodada_10[8][1], rodada_10[8][0]])
    jogos_rodada_10.append([rodada_10[11][0], rodada_10[11][1], 'x', rodada_10[9][1], rodada_10[9][0]])

    jogos_rodada_10.append([rodada_10[14][0], rodada_10[14][1], 'x', rodada_10[12][1], rodada_10[12][0]])
    jogos_rodada_10.append([rodada_10[15][0], rodada_10[15][1], 'x', rodada_10[13][1], rodada_10[13][0]])

    jogos_rodada_10.append([rodada_10[18][0], rodada_10[18][1], 'x', rodada_10[16][1], rodada_10[16][0]])
    jogos_rodada_10.append([rodada_10[19][0], rodada_10[19][1], 'x', rodada_10[17][1], rodada_10[17][0]])

    jogos_rodada_10.append([rodada_10[22][0], rodada_10[22][1], 'x', rodada_10[20][1], rodada_10[20][0]])
    jogos_rodada_10.append([rodada_10[23][0], rodada_10[23][1], 'x', rodada_10[21][1], rodada_10[21][0]])

    for x in jogos_rodada_10:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_11.append([rodada_11[3][0], rodada_11[3][1], 'x', rodada_11[0][1], rodada_11[0][0]])
    jogos_rodada_11.append([rodada_11[2][0], rodada_11[2][1], 'x', rodada_11[1][1], rodada_11[1][0]])

    jogos_rodada_11.append([rodada_11[7][0], rodada_11[7][1], 'x', rodada_11[4][1], rodada_11[4][0]])
    jogos_rodada_11.append([rodada_11[6][0], rodada_11[6][1], 'x', rodada_11[5][1], rodada_11[5][0]])

    jogos_rodada_11.append([rodada_11[11][0], rodada_11[11][1], 'x', rodada_11[8][1], rodada_11[8][0]])
    jogos_rodada_11.append([rodada_11[10][0], rodada_11[10][1], 'x', rodada_11[9][1], rodada_11[9][0]])

    jogos_rodada_11.append([rodada_11[15][0], rodada_11[15][1], 'x', rodada_11[12][1], rodada_11[12][0]])
    jogos_rodada_11.append([rodada_11[14][0], rodada_11[14][1], 'x', rodada_11[13][1], rodada_11[13][0]])

    jogos_rodada_11.append([rodada_11[19][0], rodada_11[19][1], 'x', rodada_11[16][1], rodada_11[16][0]])
    jogos_rodada_11.append([rodada_11[18][0], rodada_11[18][1], 'x', rodada_11[17][1], rodada_11[17][0]])

    jogos_rodada_11.append([rodada_11[23][0], rodada_11[23][1], 'x', rodada_11[20][1], rodada_11[20][0]])
    jogos_rodada_11.append([rodada_11[22][0], rodada_11[22][1], 'x', rodada_11[21][1], rodada_11[21][0]])

    for x in jogos_rodada_11:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    classi = {}
    for item in jogos_rodada_6 + jogos_rodada_7 + jogos_rodada_8 + jogos_rodada_9 + jogos_rodada_10 + jogos_rodada_11:
        for nome in dict_liberta_pts:
            check = nome in item
            if check:
                indice = item.index(nome)

                if nome in classi:
                    if indice == 5:
                        classi[nome].append([item[indice + 1], item[indice - 1]])
                    if indice == 1:
                        classi[nome].append([item[indice - 1], item[indice + 1]])
                else:
                    if indice == 5:
                        classi[nome] = [[item[indice + 1], item[indice - 1]]]
                    if indice == 1:
                        classi[nome] = [[item[indice - 1], item[indice + 1]]]

    classificacao = []

    for item, value in classi.items():
        vit = 0
        der = 0
        emp = 0
        soma = 0
        soma_pontos = 0.00

        for lista in value:
            vit += sum(lista.count(v) for v in lista if v == 'V')
            der += sum(lista.count(v) for v in lista if v == 'D')
            emp += sum(lista.count(v) for v in lista if v == 'E')
            soma = (3 * vit) + emp
            soma_pontos += sum(v for v in lista if isinstance(v, float))

        classificacao.append([item, vit, emp, der, soma, soma_pontos])

    g1 = []
    g2 = []
    g3 = []
    g4 = []
    g5 = []
    g6 = []

    for ind in range(0, 4):
        g1.append(classificacao[ind])
    for ind in range(4, 8):
        g2.append(classificacao[ind])
    for ind in range(8, 12):
        g3.append(classificacao[ind])
    for ind in range(12, 16):
        g4.append(classificacao[ind])
    for ind in range(16, 20):
        g5.append(classificacao[ind])
    for ind in range(20, 24):
        g6.append(classificacao[ind])

    return jogos_rodada_6, jogos_rodada_7, jogos_rodada_8, jogos_rodada_9, jogos_rodada_10, jogos_rodada_11, g1, g2, g3, g4, g5, g6


def get_class_liberta_prim_turno():
    jogos_rodada_6, jogos_rodada_7, jogos_rodada_8, jogos_rodada_9, jogos_rodada_10, jogos_rodada_11, \
    g1, g2, g3, g4, g5, g6 = get_liberta_prim_turno()

    data1 = sorted(g1, key=lambda y: (y[4], y[5]), reverse=True)
    data2 = sorted(g2, key=lambda y: (y[4], y[5]), reverse=True)
    data3 = sorted(g3, key=lambda y: (y[4], y[5]), reverse=True)
    data4 = sorted(g4, key=lambda y: (y[4], y[5]), reverse=True)
    data5 = sorted(g5, key=lambda y: (y[4], y[5]), reverse=True)
    data6 = sorted(g6, key=lambda y: (y[4], y[5]), reverse=True)

    d1 = []
    d2 = []
    d3 = []
    d4 = []
    d5 = []
    d6 = []
    r1 = []
    r2 = []
    r3 = []
    r4 = []
    r5 = []
    r6 = []

    for data in data1[0:2]:
        d1.append(data)
    for data in data1[2:4]:
        r1.append(data)

    for data in data2[0:2]:
        d2.append(data)
    for data in data2[2:4]:
        r2.append(data)

    for data in data3[0:2]:
        d3.append(data)
    for data in data3[2:4]:
        r3.append(data)

    for data in data4[0:2]:
        d4.append(data)
    for data in data4[2:4]:
        r4.append(data)

    for data in data5[0:2]:
        d5.append(data)
    for data in data5[2:4]:
        r5.append(data)

    for data in data6[0:2]:
        d6.append(data)
    for data in data6[2:4]:
        r6.append(data)

    classificados = d1 + d2 + d3 + d4 + d5 + d6
    repescagem = r1 + r2 + r3 + r4 + r5 + r6

    classi = sorted(classificados, key=lambda x: (x[4], x[5]), reverse=True)
    rep = sorted(repescagem, key=lambda x: (x[4], x[5]), reverse=True)
    classi.append(rep[0])
    classi.append(rep[1])
    classi.append(rep[2])
    classi.append(rep[3])

    class_mm = []
    for x in range(len(classi)):
        class_mm.append(classi[x][0])

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    list_oitavas = []
    for x in range(len(class_mm)):
        for ids, nomes in dict_nomes.items():
            if class_mm[x] in nomes:
                list_oitavas.append(ids)

    return list_oitavas


def oitavas_de_final_prim_turno():
    dict_oitavas_ = collections.defaultdict(list)
    dict_oitavas_pts = {}
    ordered_dict_oitavas = {}
    oitavas = []

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_oitavas_prim_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_oitavas_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_oitavas_[key].append(0.00)

    novo_dict_oitavas = dict(dict_oitavas_)

    for time_id in list(novo_dict_oitavas):
        if time_id not in list_oitavas_prim_turno:
            novo_dict_oitavas.pop(str(time_id))

    for item in list_oitavas_prim_turno:
        ordered_dict_oitavas[str(item)] = novo_dict_oitavas[str(item)]

    for chave, valor in ordered_dict_oitavas.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_oitavas_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_oitavas_prim_turno)

        for teams in threads:
            dict_oitavas_pts[teams.info.nome].append(teams.pontos)

    for key, value in dict_oitavas_pts.items():
        if not value[1]:
            oitavas.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                oitavas.append([key, value[0], value[1][0], 0.00])
            else:
                oitavas.append([key, value[0], value[1][0], value[1][1]])

    jogos_oitavas_a = []
    jogos_oitavas_a.append(
        [oitavas[0][2], oitavas[0][1], oitavas[0][0], oitavas[0][3], oitavas[15][2], oitavas[15][1], oitavas[15][0],
         oitavas[15][3]])
    jogos_oitavas_a.append(
        [oitavas[6][2], oitavas[6][1], oitavas[6][0], oitavas[6][3], oitavas[9][2], oitavas[9][1], oitavas[9][0],
         oitavas[9][3]])
    jogos_oitavas_a.append(
        [oitavas[2][2], oitavas[2][1], oitavas[2][0], oitavas[2][3], oitavas[13][2], oitavas[13][1], oitavas[13][0],
         oitavas[13][3]])
    jogos_oitavas_a.append(
        [oitavas[4][2], oitavas[4][1], oitavas[4][0], oitavas[4][3], oitavas[11][2], oitavas[11][1], oitavas[11][0],
         oitavas[11][3]])

    jogos_oitavas_b = []
    jogos_oitavas_b.append(
        [oitavas[1][3], oitavas[1][1], oitavas[1][0], oitavas[1][2], oitavas[14][3], oitavas[14][1], oitavas[14][0],
         oitavas[14][2]])
    jogos_oitavas_b.append(
        [oitavas[7][3], oitavas[7][1], oitavas[7][0], oitavas[7][2], oitavas[8][3], oitavas[8][1], oitavas[8][0],
         oitavas[8][2]])
    jogos_oitavas_b.append(
        [oitavas[3][3], oitavas[3][1], oitavas[3][0], oitavas[3][2], oitavas[12][3], oitavas[12][1], oitavas[12][0],
         oitavas[12][2]])
    jogos_oitavas_b.append(
        [oitavas[5][3], oitavas[5][1], oitavas[5][0], oitavas[5][2], oitavas[10][3], oitavas[10][1], oitavas[10][0],
         oitavas[10][2]])

    # print(jogos_oitavas_a, jogos_oitavas_b)
    return jogos_oitavas_a, jogos_oitavas_b


def get_class_oitavas():
    jogos_oitavas_a, jogos_oitavas_b = oitavas_de_final_prim_turno()

    oitavas_a = jogos_oitavas_a
    oitavas_b = jogos_oitavas_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    oit_a = {}
    for item in oitavas_a:
        if item[2] in oit_a or item[6] in oit_a:
            oit_a[item[2]].append([item[0], item[3]])
            oit_a[item[6]].append([item[4], item[7]])
        else:
            oit_a[item[2]] = [item[0], item[3]]
            oit_a[item[6]] = [item[4], item[7]]

    oit_b = {}
    for item in oitavas_b:
        if item[2] in oit_b or item[6] in oit_b:
            oit_b[item[2]].append([item[0], item[3]])
            oit_b[item[6]].append([item[4], item[7]])
        else:
            oit_b[item[2]] = [item[0], item[3]]
            oit_b[item[6]] = [item[4], item[7]]

    times_a = []
    for key, value in oit_a.items():
        times_a.append([key, value])

    times_b = []
    for key, value in oit_b.items():
        times_b.append([key, value])

    data1 = sorted(times_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_a[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data3 = sorted(times_a[4:6], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data4 = sorted(times_a[6:8], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    data5 = sorted(times_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data6 = sorted(times_b[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data7 = sorted(times_b[4:6], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data8 = sorted(times_b[6:8], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    quartas = [data1[0][0], data2[0][0], data3[0][0], data4[0][0], data5[0][0], data6[0][0], data7[0][0], data8[0][0]]

    list_quartas = []
    for x in range(len(quartas)):
        for ids, nomes in dict_nomes.items():
            if quartas[x] in nomes:
                list_quartas.append(ids)

    # print(list_quartas)
    return list_quartas


def quartas_de_final_prim_turno():
    dict_quartas_ = collections.defaultdict(list)
    dict_quartas_pts = {}
    ordered_dict_quartas = {}
    quartas = []

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_quartas_prim_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_quartas_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_quartas_[key].append(0.00)

    novo_dict_quartas = dict(dict_quartas_)

    for time_id in list(novo_dict_quartas):
        if time_id not in list_quartas_prim_turno:
            novo_dict_quartas.pop(str(time_id))

    for item in list_quartas_prim_turno:
        ordered_dict_quartas[str(item)] = novo_dict_quartas[str(item)]

    for chave, valor in ordered_dict_quartas.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_quartas_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_quartas_prim_turno)

        for teams in threads:
            dict_quartas_pts[teams.info.nome].append(teams.pontos)

    for key, value in dict_quartas_pts.items():
        if not value[1]:
            quartas.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                quartas.append([key, value[0], value[1][0], 0.00])
            else:
                quartas.append([key, value[0], value[1][0], value[1][1]])

    jogos_quartas_a = []
    jogos_quartas_a.append(
        [quartas[0][2], quartas[0][1], quartas[0][0], quartas[0][3], quartas[1][2], quartas[1][1], quartas[1][0],
         quartas[1][3]])
    jogos_quartas_a.append(
        [quartas[2][2], quartas[2][1], quartas[2][0], quartas[2][3], quartas[3][2], quartas[3][1], quartas[3][0],
         quartas[3][3]])

    jogos_quartas_b = []
    jogos_quartas_b.append(
        [quartas[4][3], quartas[4][1], quartas[4][0], quartas[4][2], quartas[5][3], quartas[5][1], quartas[5][0],
         quartas[5][2]])
    jogos_quartas_b.append(
        [quartas[6][3], quartas[6][1], quartas[6][0], quartas[6][2], quartas[7][3], quartas[7][1], quartas[7][0],
         quartas[7][2]])

    # print(jogos_quartas_a, jogos_quartas_b)
    return jogos_quartas_a, jogos_quartas_b


def get_class_quartas():
    jogos_quartas_a, jogos_quartas_b = quartas_de_final_prim_turno()
    quartas_a = jogos_quartas_a
    quartas_b = jogos_quartas_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    qua_a = {}
    for item in quartas_a:
        if item[2] in qua_a or item[6] in qua_a:
            qua_a[item[2]].append([item[0], item[3]])
            qua_a[item[6]].append([item[4], item[7]])
        else:
            qua_a[item[2]] = [item[0], item[3]]
            qua_a[item[6]] = [item[4], item[7]]

    qua_b = {}
    for item in quartas_b:
        if item[2] in qua_b or item[6] in qua_b:
            qua_b[item[2]].append([item[0], item[3]])
            qua_b[item[6]].append([item[4], item[7]])
        else:
            qua_b[item[2]] = [item[0], item[3]]
            qua_b[item[6]] = [item[4], item[7]]

    times_quartas_a = []
    for key, value in qua_a.items():
        times_quartas_a.append([key, value])

    times_quartas_b = []
    for key, value in qua_b.items():
        times_quartas_b.append([key, value])

    data1 = sorted(times_quartas_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_quartas_a[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data3 = sorted(times_quartas_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data4 = sorted(times_quartas_b[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    quartas = [data1[0][0], data2[0][0], data3[0][0], data4[0][0]]

    list_semis = []
    for x in range(len(quartas)):
        for ids, nomes in dict_nomes.items():
            if quartas[x] in nomes:
                list_semis.append(ids)

    # print(list_semis)
    return list_semis


def semi_finais_prim_turno():
    dict_semis_ = collections.defaultdict(list)
    dict_semis_pts = {}
    ordered_dict_semis = {}
    semis = []

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_semis_prim_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_semis_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_semis_[key].append(0.00)

    novo_dict_semis = dict(dict_semis_)

    for time_id in list(novo_dict_semis):
        if time_id not in list_semis_prim_turno:
            novo_dict_semis.pop(str(time_id))

    for item in list_semis_prim_turno:
        ordered_dict_semis[str(item)] = novo_dict_semis[str(item)]

    for chave, valor in ordered_dict_semis.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_semis_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_semis_prim_turno)

        for teams in threads:
            dict_semis_pts[teams.info.nome].append(teams.pontos)

    for key, value in dict_semis_pts.items():
        if not value[1]:
            semis.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                semis.append([key, value[0], value[1][0], 0.00])
            else:
                semis.append([key, value[0], value[1][0], value[1][1]])

    jogos_semis_a = []
    jogos_semis_a.append(
        [semis[0][2], semis[0][1], semis[0][0], semis[0][3], semis[1][2], semis[1][1], semis[1][0],
         semis[1][3]])

    jogos_semis_b = []
    jogos_semis_b.append(
        [semis[2][2], semis[2][1], semis[2][0], semis[2][3], semis[3][2], semis[3][1], semis[3][0],
         semis[3][3]])

    # print(jogos_semis_a, jogos_semis_b)
    return jogos_semis_a, jogos_semis_b


def get_class_semis():
    jogos_semis_a, jogos_semis_b = semi_finais_prim_turno()
    semis_a = jogos_semis_a
    semis_b = jogos_semis_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    finais_a = {}
    for item in semis_a:
        if item[2] in finais_a or item[6] in finais_a:
            finais_a[item[2]].append([item[0], item[3]])
            finais_a[item[6]].append([item[4], item[7]])
        else:
            finais_a[item[2]] = [item[0], item[3]]
            finais_a[item[6]] = [item[4], item[7]]

    finais_b = {}
    for item in semis_b:
        if item[2] in finais_b or item[6] in finais_b:
            finais_b[item[2]].append([item[0], item[3]])
            finais_b[item[6]].append([item[4], item[7]])
        else:
            finais_b[item[2]] = [item[0], item[3]]
            finais_b[item[6]] = [item[4], item[7]]

    times_finais_a = []
    for key, value in finais_a.items():
        times_finais_a.append([key, value])

    times_finais_b = []
    for key, value in finais_b.items():
        times_finais_b.append([key, value])

    data1 = sorted(times_finais_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_finais_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    semis = [data1[0][0], data2[0][0]]

    list_finais = []
    for x in range(len(semis)):
        for ids, nomes in dict_nomes.items():
            if semis[x] in nomes:
                list_finais.append(ids)

    # print(list_finais)
    return list_finais


def finais_prim_turno():
    dict_finais_ = collections.defaultdict(list)
    dict_finais_pts = {}
    ordered_dict_finais = {}
    finais = []

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_finais_prim_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_finais_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_finais_[key].append(0.00)

    novo_dict_finais = dict(dict_finais_)

    for time_id in list(novo_dict_finais):
        if time_id not in list_finais_prim_turno:
            novo_dict_finais.pop(str(time_id))

    for item in list_finais_prim_turno:
        ordered_dict_finais[str(item)] = novo_dict_finais[str(item)]

    for chave, valor in ordered_dict_finais.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_finais_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_finais_prim_turno)

        for teams in threads:
            dict_finais_pts[teams.info.nome].append(teams.pontos)

    for key, value in dict_finais_pts.items():
        if not value[1]:
            finais.append([key, value[0], 0.00, 0.00])
        else:
            if len(value[1]) == 1:
                finais.append([key, value[0], value[1][0], 0.00])
            else:
                finais.append([key, value[0], value[1][0], value[1][1]])

    jogos_final_a = []
    jogos_final_a.append(
        [finais[0][2], finais[0][1], finais[0][0], finais[0][3]])

    jogos_final_b = []
    jogos_final_b.append(
        [finais[1][3], finais[1][1], finais[1][0], finais[1][2]])

    esq_maior = False
    if jogos_final_a[0][0] + jogos_final_a[0][3] > jogos_final_b[0][0] + jogos_final_b[0][3]:
        esq_maior = True

    # print(jogos_final_a, jogos_final_b, esq_maior)
    return jogos_final_a, jogos_final_b, esq_maior


def mata_mata_prim_turno():
    jogos_oitavas_a, jogos_oitavas_b = oitavas_de_final_prim_turno()
    jogos_quartas_a, jogos_quartas_b = quartas_de_final_prim_turno()
    jogos_semis_a, jogos_semis_b = semi_finais_prim_turno()
    jogos_final_a, jogos_final_b, esq_maior = finais_prim_turno()
    campeao_prim_turno = ''
    vice_prim_turno = ''

    for f_a, f_b in zip(jogos_final_a, jogos_final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao_prim_turno = f_a[2]
            vice_prim_turno = f_b[2]
        else:
            campeao_prim_turno = f_b[2]
            vice_prim_turno = f_a[2]

    dict_prem['liberta_prim_turno']['campeao'] = campeao_prim_turno
    dict_prem['liberta_prim_turno']['vice'] = vice_prim_turno

    with open(f'static/dict_prem.json', 'w', encoding='utf-8') as f:
        json.dump(dict_prem, f)

    # print(jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, jogos_final_a, jogos_final_b, esq_maior)
    return jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, jogos_final_a, jogos_final_b, esq_maior


def get_parciais(time_id):
    # return_parciais = [api.time_parcial(time_id)]
    return api.time_parcial(time_id)


def get_liberta_seg_turno():
    dict_liberta_ = collections.defaultdict(list)
    dict_liberta_pts = {}
    dict_liberta = {}
    ordered_dict_liberta = {}
    dict_parciais = {}

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for item in rodadas_liberta_seg_turno:

        if str(item) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(item)]
                dict_liberta_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_liberta_[key].append(0.00)

    for time_id in list(dict(dict_liberta_)):
        if int(time_id) not in grupo_liberta_seg_turno:
            dict(dict_liberta_).pop(str(time_id))

    for item in grupo_liberta_seg_turno:
        ordered_dict_liberta[str(item)] = dict(dict_liberta_)[str(item)]

    # for chave, valor in ordered_dict_liberta.items():
    #     for c, v in json.loads(escudos).items():
    #         for id, nome in json.loads(nomes).items():
    #             if chave == c:
    #                 if chave == id:
    #                     dict_liberta_pts[nome] = [v, valor]

    rodada_25 = []
    rodada_26 = []
    rodada_27 = []
    rodada_28 = []
    rodada_29 = []
    rodada_30 = []
    jogos_rodada_25 = []
    jogos_rodada_26 = []
    jogos_rodada_27 = []
    jogos_rodada_28 = []
    jogos_rodada_29 = []
    jogos_rodada_30 = []

    if api.mercado().status.nome == 'Mercado fechado':

        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(get_parciais, grupo_liberta_seg_turno)

            # start_time = timeit.default_timer()

            for teams in threads:
                ordered_dict_liberta[str(teams.info.id)].append(teams.pontos)

            # print(timeit.default_timer() - start_time)

        for chave, valor in ordered_dict_liberta.items():
            for c, v in json.loads(escudos).items():
                for id, nome in json.loads(nomes).items():
                    if chave == c:
                        if chave == id:
                            dict_liberta_pts[nome] = [v, valor]

        for key, value in dict_liberta_pts.items():
            rodada_25.append([key, float(value[1][6]) if rod == 25 else float(value[1][0])])
            rodada_26.append([key, float(value[1][6]) if rod == 26 else float(value[1][1])])
            rodada_27.append([key, float(value[1][6]) if rod == 27 else float(value[1][2])])
            rodada_28.append([key, float(value[1][6]) if rod == 28 else float(value[1][3])])
            rodada_29.append([key, float(value[1][6]) if rod == 29 else float(value[1][4])])
            rodada_30.append([key, float(value[1][6]) if rod == 30 else float(value[1][5])])

    if api.mercado().status.nome == 'Mercado aberto' or api.mercado().status.nome == 'Final de temporada':

        for chave, valor in ordered_dict_liberta.items():
            for c, v in json.loads(escudos).items():
                for id, nome in json.loads(nomes).items():
                    if chave == c:
                        if chave == id:
                            dict_liberta_pts[nome] = [v, valor]

        for key, value in dict_liberta_pts.items():
            rodada_25.append([key, float(value[1][0])])
            rodada_26.append([key, float(value[1][1])])
            rodada_27.append([key, float(value[1][2])])
            rodada_28.append([key, float(value[1][3])])
            rodada_29.append([key, float(value[1][4])])
            rodada_30.append([key, float(value[1][5])])

    jogos_rodada_25.append([rodada_25[0][0], rodada_25[0][1], 'x', rodada_25[1][1], rodada_25[1][0]])
    jogos_rodada_25.append([rodada_25[2][0], rodada_25[2][1], 'x', rodada_25[3][1], rodada_25[3][0]])
    jogos_rodada_25.append([rodada_25[4][0], rodada_25[4][1], 'x', rodada_25[5][1], rodada_25[5][0]])
    jogos_rodada_25.append([rodada_25[6][0], rodada_25[6][1], 'x', rodada_25[7][1], rodada_25[7][0]])
    jogos_rodada_25.append([rodada_25[8][0], rodada_25[8][1], 'x', rodada_25[9][1], rodada_25[9][0]])
    jogos_rodada_25.append([rodada_25[10][0], rodada_25[10][1], 'x', rodada_25[11][1], rodada_25[11][0]])
    jogos_rodada_25.append([rodada_25[12][0], rodada_25[12][1], 'x', rodada_25[13][1], rodada_25[13][0]])
    jogos_rodada_25.append([rodada_25[14][0], rodada_25[14][1], 'x', rodada_25[15][1], rodada_25[15][0]])
    jogos_rodada_25.append([rodada_25[16][0], rodada_25[16][1], 'x', rodada_25[17][1], rodada_25[17][0]])
    jogos_rodada_25.append([rodada_25[18][0], rodada_25[18][1], 'x', rodada_25[19][1], rodada_25[19][0]])
    jogos_rodada_25.append([rodada_25[20][0], rodada_25[20][1], 'x', rodada_25[21][1], rodada_25[21][0]])
    jogos_rodada_25.append([rodada_25[22][0], rodada_25[22][1], 'x', rodada_25[23][1], rodada_25[23][0]])

    empate = False
    for x in jogos_rodada_25:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_26.append([rodada_26[0][0], rodada_26[0][1], 'x', rodada_26[2][1], rodada_26[2][0]])
    jogos_rodada_26.append([rodada_26[1][0], rodada_26[1][1], 'x', rodada_26[3][1], rodada_26[3][0]])

    jogos_rodada_26.append([rodada_26[4][0], rodada_26[4][1], 'x', rodada_26[6][1], rodada_26[6][0]])
    jogos_rodada_26.append([rodada_26[5][0], rodada_26[5][1], 'x', rodada_26[7][1], rodada_26[7][0]])

    jogos_rodada_26.append([rodada_26[8][0], rodada_26[8][1], 'x', rodada_26[10][1], rodada_26[10][0]])
    jogos_rodada_26.append([rodada_26[9][0], rodada_26[9][1], 'x', rodada_26[11][1], rodada_26[11][0]])

    jogos_rodada_26.append([rodada_26[12][0], rodada_26[12][1], 'x', rodada_26[14][1], rodada_26[14][0]])
    jogos_rodada_26.append([rodada_26[13][0], rodada_26[13][1], 'x', rodada_26[15][1], rodada_26[15][0]])

    jogos_rodada_26.append([rodada_26[16][0], rodada_26[16][1], 'x', rodada_26[18][1], rodada_26[18][0]])
    jogos_rodada_26.append([rodada_26[17][0], rodada_26[17][1], 'x', rodada_26[19][1], rodada_26[19][0]])

    jogos_rodada_26.append([rodada_26[20][0], rodada_26[20][1], 'x', rodada_26[22][1], rodada_26[22][0]])
    jogos_rodada_26.append([rodada_26[21][0], rodada_26[21][1], 'x', rodada_26[23][1], rodada_26[23][0]])

    empate = False
    for x in jogos_rodada_26:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_27.append([rodada_27[0][0], rodada_27[0][1], 'x', rodada_27[3][1], rodada_27[3][0]])
    jogos_rodada_27.append([rodada_27[1][0], rodada_27[1][1], 'x', rodada_27[2][1], rodada_27[2][0]])

    jogos_rodada_27.append([rodada_27[4][0], rodada_27[4][1], 'x', rodada_27[7][1], rodada_27[7][0]])
    jogos_rodada_27.append([rodada_27[5][0], rodada_27[5][1], 'x', rodada_27[6][1], rodada_27[6][0]])

    jogos_rodada_27.append([rodada_27[8][0], rodada_27[8][1], 'x', rodada_27[11][1], rodada_27[11][0]])
    jogos_rodada_27.append([rodada_27[9][0], rodada_27[9][1], 'x', rodada_27[10][1], rodada_27[10][0]])

    jogos_rodada_27.append([rodada_27[12][0], rodada_27[12][1], 'x', rodada_27[15][1], rodada_27[15][0]])
    jogos_rodada_27.append([rodada_27[13][0], rodada_27[13][1], 'x', rodada_27[14][1], rodada_27[14][0]])

    jogos_rodada_27.append([rodada_27[16][0], rodada_27[16][1], 'x', rodada_27[19][1], rodada_27[19][0]])
    jogos_rodada_27.append([rodada_27[17][0], rodada_27[17][1], 'x', rodada_27[18][1], rodada_27[18][0]])

    jogos_rodada_27.append([rodada_27[20][0], rodada_27[20][1], 'x', rodada_27[23][1], rodada_27[23][0]])
    jogos_rodada_27.append([rodada_27[21][0], rodada_27[21][1], 'x', rodada_27[22][1], rodada_27[22][0]])

    for x in jogos_rodada_27:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_28.append([rodada_28[1][0], rodada_28[1][1], 'x', rodada_28[0][1], rodada_28[0][0]])
    jogos_rodada_28.append([rodada_28[3][0], rodada_28[3][1], 'x', rodada_28[2][1], rodada_28[2][0]])

    jogos_rodada_28.append([rodada_28[5][0], rodada_28[5][1], 'x', rodada_28[4][1], rodada_28[4][0]])
    jogos_rodada_28.append([rodada_28[7][0], rodada_28[7][1], 'x', rodada_28[6][1], rodada_28[6][0]])

    jogos_rodada_28.append([rodada_28[9][0], rodada_28[9][1], 'x', rodada_28[8][1], rodada_28[8][0]])
    jogos_rodada_28.append([rodada_28[11][0], rodada_28[11][1], 'x', rodada_28[10][1], rodada_28[10][0]])

    jogos_rodada_28.append([rodada_28[13][0], rodada_28[13][1], 'x', rodada_28[12][1], rodada_28[12][0]])
    jogos_rodada_28.append([rodada_28[15][0], rodada_28[15][1], 'x', rodada_28[14][1], rodada_28[14][0]])

    jogos_rodada_28.append([rodada_28[17][0], rodada_28[17][1], 'x', rodada_28[16][1], rodada_28[16][0]])
    jogos_rodada_28.append([rodada_28[19][0], rodada_28[19][1], 'x', rodada_28[18][1], rodada_28[18][0]])

    jogos_rodada_28.append([rodada_28[21][0], rodada_28[21][1], 'x', rodada_28[20][1], rodada_28[20][0]])
    jogos_rodada_28.append([rodada_28[23][0], rodada_28[23][1], 'x', rodada_28[22][1], rodada_28[22][0]])

    for x in jogos_rodada_28:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_29.append([rodada_29[2][0], rodada_29[2][1], 'x', rodada_29[0][1], rodada_29[0][0]])
    jogos_rodada_29.append([rodada_29[3][0], rodada_29[3][1], 'x', rodada_29[1][1], rodada_29[1][0]])

    jogos_rodada_29.append([rodada_29[6][0], rodada_29[6][1], 'x', rodada_29[4][1], rodada_29[4][0]])
    jogos_rodada_29.append([rodada_29[7][0], rodada_29[7][1], 'x', rodada_29[5][1], rodada_29[5][0]])

    jogos_rodada_29.append([rodada_29[10][0], rodada_29[10][1], 'x', rodada_29[8][1], rodada_29[8][0]])
    jogos_rodada_29.append([rodada_29[11][0], rodada_29[11][1], 'x', rodada_29[9][1], rodada_29[9][0]])

    jogos_rodada_29.append([rodada_29[14][0], rodada_29[14][1], 'x', rodada_29[12][1], rodada_29[12][0]])
    jogos_rodada_29.append([rodada_29[15][0], rodada_29[15][1], 'x', rodada_29[13][1], rodada_29[13][0]])

    jogos_rodada_29.append([rodada_29[18][0], rodada_29[18][1], 'x', rodada_29[16][1], rodada_29[16][0]])
    jogos_rodada_29.append([rodada_29[19][0], rodada_29[19][1], 'x', rodada_29[17][1], rodada_29[17][0]])

    jogos_rodada_29.append([rodada_29[22][0], rodada_29[22][1], 'x', rodada_29[20][1], rodada_29[20][0]])
    jogos_rodada_29.append([rodada_29[23][0], rodada_29[23][1], 'x', rodada_29[21][1], rodada_29[21][0]])

    for x in jogos_rodada_29:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    jogos_rodada_30.append([rodada_30[3][0], rodada_30[3][1], 'x', rodada_30[0][1], rodada_30[0][0]])
    jogos_rodada_30.append([rodada_30[2][0], rodada_30[2][1], 'x', rodada_30[1][1], rodada_30[1][0]])

    jogos_rodada_30.append([rodada_30[7][0], rodada_30[7][1], 'x', rodada_30[4][1], rodada_30[4][0]])
    jogos_rodada_30.append([rodada_30[6][0], rodada_30[6][1], 'x', rodada_30[5][1], rodada_30[5][0]])

    jogos_rodada_30.append([rodada_30[11][0], rodada_30[11][1], 'x', rodada_30[8][1], rodada_30[8][0]])
    jogos_rodada_30.append([rodada_30[10][0], rodada_30[10][1], 'x', rodada_30[9][1], rodada_30[9][0]])

    jogos_rodada_30.append([rodada_30[15][0], rodada_30[15][1], 'x', rodada_30[12][1], rodada_30[12][0]])
    jogos_rodada_30.append([rodada_30[14][0], rodada_30[14][1], 'x', rodada_30[13][1], rodada_30[13][0]])

    jogos_rodada_30.append([rodada_30[19][0], rodada_30[19][1], 'x', rodada_30[16][1], rodada_30[16][0]])
    jogos_rodada_30.append([rodada_30[18][0], rodada_30[18][1], 'x', rodada_30[17][1], rodada_30[17][0]])

    jogos_rodada_30.append([rodada_30[23][0], rodada_30[23][1], 'x', rodada_30[20][1], rodada_30[20][0]])
    jogos_rodada_30.append([rodada_30[22][0], rodada_30[22][1], 'x', rodada_30[21][1], rodada_30[21][0]])

    for x in jogos_rodada_30:
        maior_man = x[1] > x[3]
        maior_vis = x[1] < x[3]
        menor_man = x[1] < x[3]
        menor_vis = x[1] > x[3]
        empate = x[1] == x[3]
        if maior_man:
            x.insert(0, 'V')
        if maior_vis:
            x.insert(6, 'V')
        if menor_man:
            x.insert(0, 'D')
        if menor_vis:
            x.insert(6, 'D')
        if empate and (isinstance(x[1], float) and isinstance(x[3], float)) and (x[1] or x[3]) != 0:
            x.insert(0, 'E')
            x.insert(6, 'E')
        if x[1] == '' or x[3] == '' or x[1] == 0 or x[3] == 0:
            x.insert(0, '')
            x.insert(6, '')

    classi = {}
    for item in jogos_rodada_25 + jogos_rodada_26 + jogos_rodada_27 + jogos_rodada_28 + jogos_rodada_29 + jogos_rodada_30:
        for nome in dict_liberta_pts:
            check = nome in item
            if check:
                indice = item.index(nome)

                if nome in classi:
                    if indice == 5:
                        classi[nome].append([item[indice + 1], item[indice - 1]])
                    if indice == 1:
                        classi[nome].append([item[indice - 1], item[indice + 1]])
                else:
                    if indice == 5:
                        classi[nome] = [[item[indice + 1], item[indice - 1]]]
                    if indice == 1:
                        classi[nome] = [[item[indice - 1], item[indice + 1]]]

    classificacao = []

    for item, value in classi.items():
        vit = 0
        der = 0
        emp = 0
        soma = 0
        soma_pontos = 0.00

        for lista in value:
            vit += sum(lista.count(v) for v in lista if v == 'V')
            der += sum(lista.count(v) for v in lista if v == 'D')
            emp += sum(lista.count(v) for v in lista if v == 'E')
            soma = (3 * vit) + emp
            soma_pontos += sum(v for v in lista if isinstance(v, float))

        classificacao.append([item, vit, emp, der, soma, soma_pontos])

    g1 = []
    g2 = []
    g3 = []
    g4 = []
    g5 = []
    g6 = []

    for ind in range(0, 4):
        g1.append(classificacao[ind])
    for ind in range(4, 8):
        g2.append(classificacao[ind])
    for ind in range(8, 12):
        g3.append(classificacao[ind])
    for ind in range(12, 16):
        g4.append(classificacao[ind])
    for ind in range(16, 20):
        g5.append(classificacao[ind])
    for ind in range(20, 24):
        g6.append(classificacao[ind])

    return jogos_rodada_25, jogos_rodada_26, jogos_rodada_27, jogos_rodada_28, jogos_rodada_29, jogos_rodada_30, g1, g2, g3, g4, g5, g6


def get_class_liberta_seg_turno():
    jogos_rodada_25, jogos_rodada_26, jogos_rodada_27, jogos_rodada_28, jogos_rodada_29, jogos_rodada_30, g1, g2, g3, g4, g5, g6 = get_liberta_seg_turno()

    data1 = sorted(g1, key=lambda y: (y[4], y[5]), reverse=True)
    data2 = sorted(g2, key=lambda y: (y[4], y[5]), reverse=True)
    data3 = sorted(g3, key=lambda y: (y[4], y[5]), reverse=True)
    data4 = sorted(g4, key=lambda y: (y[4], y[5]), reverse=True)
    data5 = sorted(g5, key=lambda y: (y[4], y[5]), reverse=True)
    data6 = sorted(g6, key=lambda y: (y[4], y[5]), reverse=True)

    d1 = []
    d2 = []
    d3 = []
    d4 = []
    d5 = []
    d6 = []
    r1 = []
    r2 = []
    r3 = []
    r4 = []
    r5 = []
    r6 = []

    for data in data1[0:2]:
        d1.append(data)
    for data in data1[2:4]:
        r1.append(data)

    for data in data2[0:2]:
        d2.append(data)
    for data in data2[2:4]:
        r2.append(data)

    for data in data3[0:2]:
        d3.append(data)
    for data in data3[2:4]:
        r3.append(data)

    for data in data4[0:2]:
        d4.append(data)
    for data in data4[2:4]:
        r4.append(data)

    for data in data5[0:2]:
        d5.append(data)
    for data in data5[2:4]:
        r5.append(data)

    for data in data6[0:2]:
        d6.append(data)
    for data in data6[2:4]:
        r6.append(data)

    classificados = d1 + d2 + d3 + d4 + d5 + d6
    repescagem = r1 + r2 + r3 + r4 + r5 + r6

    classi = sorted(classificados, key=lambda x: (x[4], x[5]), reverse=True)
    rep = sorted(repescagem, key=lambda x: (x[4], x[5]), reverse=True)
    classi.append(rep[0])
    classi.append(rep[1])
    classi.append(rep[2])
    classi.append(rep[3])

    class_mm = []
    for x in range(len(classi)):
        class_mm.append(classi[x][0])

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    list_oitavas = []
    for x in range(len(class_mm)):
        for ids, nomes in dict_nomes.items():
            if class_mm[x] in nomes:
                list_oitavas.append(ids)

    return list_oitavas


def oitavas_de_final_seg_turno():
    dict_oitavas_ = collections.defaultdict(list)
    dict_oitavas_pts = {}
    ordered_dict_oitavas = {}
    oitavas = []
    dict_matamata_oitavas = {}

    with open('static/dict_matamata.json', encoding='utf-8', mode='r') as currentFile:
        data_matamata = currentFile.read().replace('\n', '')

        for x, y in json.loads(data_matamata).items():
            dict_matamata_oitavas[x] = y

    if len(dict_matamata_oitavas['oitavas']) == 0:
        dict_matamata['oitavas'] = get_class_liberta_seg_turno()

        with open(f'static/dict_matamata.json', 'w') as f:
            json.dump(dict_matamata, f)

        list_oitavas_seg_turno = dict_matamata['oitavas']

    else:
        list_oitavas_seg_turno = dict_matamata_oitavas['oitavas']

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for rod_oit in rodadas_oitavas_seg_turno:

        if str(rod_oit) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(rod_oit)]
                dict_oitavas_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_oitavas_[key].append(0.00)

    novo_dict_oitavas = dict(dict_oitavas_)

    for time_id in list(novo_dict_oitavas):
        if time_id not in list_oitavas_seg_turno:
            novo_dict_oitavas.pop(str(time_id))

    for item in list_oitavas_seg_turno:
        ordered_dict_oitavas[str(item)] = novo_dict_oitavas[str(item)]

    for chave, valor in ordered_dict_oitavas.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_oitavas_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_oitavas_seg_turno)
            # threads = executor.map(get_parciais, list_oitavas_seg_turno)

        for teams in threads:
            dict_oitavas_pts[teams.info.nome][1].append(teams.pontos)

    for key, value in dict_oitavas_pts.items():
        oitavas.append([key,
                        value[0],
                        value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 31 else value[1][0],
                        value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 32 else value[1][1]]
                       )

    jogos_oitavas_a = []
    jogos_oitavas_a.append(
        [oitavas[0][2], oitavas[0][1], oitavas[0][0], oitavas[0][3], oitavas[15][2], oitavas[15][1], oitavas[15][0],
         oitavas[15][3]])
    jogos_oitavas_a.append(
        [oitavas[6][2], oitavas[6][1], oitavas[6][0], oitavas[6][3], oitavas[9][2], oitavas[9][1], oitavas[9][0],
         oitavas[9][3]])
    jogos_oitavas_a.append(
        [oitavas[2][2], oitavas[2][1], oitavas[2][0], oitavas[2][3], oitavas[13][2], oitavas[13][1], oitavas[13][0],
         oitavas[13][3]])
    jogos_oitavas_a.append(
        [oitavas[4][2], oitavas[4][1], oitavas[4][0], oitavas[4][3], oitavas[11][2], oitavas[11][1], oitavas[11][0],
         oitavas[11][3]])

    jogos_oitavas_b = []
    jogos_oitavas_b.append(
        [oitavas[1][3], oitavas[1][1], oitavas[1][0], oitavas[1][2], oitavas[14][3], oitavas[14][1], oitavas[14][0],
         oitavas[14][2]])
    jogos_oitavas_b.append(
        [oitavas[7][3], oitavas[7][1], oitavas[7][0], oitavas[7][2], oitavas[8][3], oitavas[8][1], oitavas[8][0],
         oitavas[8][2]])
    jogos_oitavas_b.append(
        [oitavas[3][3], oitavas[3][1], oitavas[3][0], oitavas[3][2], oitavas[12][3], oitavas[12][1], oitavas[12][0],
         oitavas[12][2]])
    jogos_oitavas_b.append(
        [oitavas[5][3], oitavas[5][1], oitavas[5][0], oitavas[5][2], oitavas[10][3], oitavas[10][1], oitavas[10][0],
         oitavas[10][2]])

    # print(jogos_oitavas_a, jogos_oitavas_b)
    return jogos_oitavas_a, jogos_oitavas_b


def get_class_oitavas_seg_turno():
    jogos_oitavas_a, jogos_oitavas_b = oitavas_de_final_seg_turno()

    oitavas_a = jogos_oitavas_a
    oitavas_b = jogos_oitavas_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    oit_a = {}
    for item in oitavas_a:
        if item[2] in oit_a or item[6] in oit_a:
            oit_a[item[2]].append([item[0], item[3]])
            oit_a[item[6]].append([item[4], item[7]])
        else:
            oit_a[item[2]] = [item[0], item[3]]
            oit_a[item[6]] = [item[4], item[7]]

    oit_b = {}
    for item in oitavas_b:
        if item[2] in oit_b or item[6] in oit_b:
            oit_b[item[2]].append([item[0], item[3]])
            oit_b[item[6]].append([item[4], item[7]])
        else:
            oit_b[item[2]] = [item[0], item[3]]
            oit_b[item[6]] = [item[4], item[7]]

    times_a = []
    for key, value in oit_a.items():
        times_a.append([key, value])

    times_b = []
    for key, value in oit_b.items():
        times_b.append([key, value])

    data1 = sorted(times_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_a[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data3 = sorted(times_a[4:6], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data4 = sorted(times_a[6:8], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    data5 = sorted(times_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data6 = sorted(times_b[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data7 = sorted(times_b[4:6], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data8 = sorted(times_b[6:8], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    quartas = [data1[0][0], data2[0][0], data3[0][0], data4[0][0], data5[0][0], data6[0][0], data7[0][0], data8[0][0]]

    list_quartas = []
    for x in range(len(quartas)):
        for ids, nomes in dict_nomes.items():
            if quartas[x] in nomes:
                list_quartas.append(ids)

    return list_quartas


def quartas_de_final_seg_turno():
    dict_quartas_ = collections.defaultdict(list)
    dict_quartas_pts = {}
    ordered_dict_quartas = {}
    quartas = []
    dict_matamata_quartas = {}

    with open('static/dict_matamata.json', encoding='utf-8', mode='r') as currentFile:
        data_matamata = currentFile.read().replace('\n', '')

        for x, y in json.loads(data_matamata).items():
            dict_matamata_quartas[x] = y

    if len(dict_matamata_quartas['quartas']) == 0:
        dict_matamata['quartas'] = get_class_oitavas_seg_turno()

        with open(f'static/dict_matamata.json', 'w') as f:
            json.dump(dict_matamata, f)

        list_quartas_seg_turno = dict_matamata['quartas']

    else:
        list_quartas_seg_turno = dict_matamata_quartas['quartas']

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for rod_qua in rodadas_quartas_seg_turno:

        if str(rod_qua) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(rod_qua)]
                dict_quartas_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_quartas_[key].append(0.00)

    novo_dict_quartas = dict(dict_quartas_)

    for time_id in list(novo_dict_quartas):
        if time_id not in list_quartas_seg_turno:
            novo_dict_quartas.pop(str(time_id))

    for item in list_quartas_seg_turno:
        ordered_dict_quartas[str(item)] = novo_dict_quartas[str(item)]

    for chave, valor in ordered_dict_quartas.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_quartas_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_quartas_seg_turno)
            # threads = executor.map(get_parciais, list_oitavas_seg_turno)

        for teams in threads:
            dict_quartas_pts[teams.info.nome][1].append(teams.pontos)

    for key, value in dict_quartas_pts.items():
        quartas.append([key,
                        value[0],
                        value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 33 else value[1][0],
                        value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 34 else value[1][1]]
                       )

    jogos_quartas_a = []
    jogos_quartas_a.append(
        [quartas[0][2], quartas[0][1], quartas[0][0], quartas[0][3], quartas[1][2], quartas[1][1], quartas[1][0],
         quartas[1][3]])
    jogos_quartas_a.append(
        [quartas[2][2], quartas[2][1], quartas[2][0], quartas[2][3], quartas[3][2], quartas[3][1], quartas[3][0],
         quartas[3][3]])

    jogos_quartas_b = []
    jogos_quartas_b.append(
        [quartas[4][3], quartas[4][1], quartas[4][0], quartas[4][2], quartas[5][3], quartas[5][1], quartas[5][0],
         quartas[5][2]])
    jogos_quartas_b.append(
        [quartas[6][3], quartas[6][1], quartas[6][0], quartas[6][2], quartas[7][3], quartas[7][1], quartas[7][0],
         quartas[7][2]])

    return jogos_quartas_a, jogos_quartas_b


def get_class_quartas_seg_turno():
    jogos_quartas_a, jogos_quartas_b = quartas_de_final_seg_turno()
    quartas_a = jogos_quartas_a
    quartas_b = jogos_quartas_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    qua_a = {}
    for item in quartas_a:
        if item[2] in qua_a or item[6] in qua_a:
            qua_a[item[2]].append([item[0], item[3]])
            qua_a[item[6]].append([item[4], item[7]])
        else:
            qua_a[item[2]] = [item[0], item[3]]
            qua_a[item[6]] = [item[4], item[7]]

    qua_b = {}
    for item in quartas_b:
        if item[2] in qua_b or item[6] in qua_b:
            qua_b[item[2]].append([item[0], item[3]])
            qua_b[item[6]].append([item[4], item[7]])
        else:
            qua_b[item[2]] = [item[0], item[3]]
            qua_b[item[6]] = [item[4], item[7]]

    times_quartas_a = []
    for key, value in qua_a.items():
        times_quartas_a.append([key, value])

    times_quartas_b = []
    for key, value in qua_b.items():
        times_quartas_b.append([key, value])

    data1 = sorted(times_quartas_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_quartas_a[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data3 = sorted(times_quartas_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data4 = sorted(times_quartas_b[2:4], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    quartas = [data1[0][0], data2[0][0], data3[0][0], data4[0][0]]

    list_semis = []
    for x in range(len(quartas)):
        for ids, nomes in dict_nomes.items():
            if quartas[x] in nomes:
                list_semis.append(ids)

    return list_semis


def semi_finais_seg_turno():
    dict_semis_ = collections.defaultdict(list)
    dict_semis_pts = {}
    ordered_dict_semis = {}
    semis = []
    dict_matamata_semis = {}

    with open('static/dict_matamata.json', encoding='utf-8', mode='r') as currentFile:
        data_matamata = currentFile.read().replace('\n', '')

        for x, y in json.loads(data_matamata).items():
            dict_matamata_semis[x] = y

    if len(dict_matamata_semis['semis']) == 0:
        dict_matamata['semis'] = get_class_quartas_seg_turno()

        with open(f'static/dict_matamata.json', 'w') as f:
            json.dump(dict_matamata, f)

        list_semis_seg_turno = dict_matamata['semis']

    else:
        list_semis_seg_turno = dict_matamata_semis['semis']

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for rod_semis in rodadas_semis_seg_turno:

        if str(rod_semis) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(rod_semis)]
                dict_semis_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_semis_[key].append(0.00)

    novo_dict_semis = dict(dict_semis_)

    for time_id in list(novo_dict_semis):
        if time_id not in list_semis_seg_turno:
            novo_dict_semis.pop(str(time_id))

    for item in list_semis_seg_turno:
        ordered_dict_semis[str(item)] = novo_dict_semis[str(item)]

    for chave, valor in ordered_dict_semis.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_semis_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_semis_seg_turno)
            # threads = executor.map(get_parciais, list_oitavas_seg_turno)

        for teams in threads:
            dict_semis_pts[teams.info.nome][1].append(teams.pontos)

    for key, value in dict_semis_pts.items():
        semis.append([key,
                      value[0],
                      value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 35 else value[1][0],
                      value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 36 else value[1][1]]
                     )

    jogos_semis_a = []
    jogos_semis_a.append(
        [semis[0][2], semis[0][1], semis[0][0], semis[0][3], semis[1][2], semis[1][1], semis[1][0],
         semis[1][3]])

    jogos_semis_b = []
    jogos_semis_b.append(
        [semis[2][3], semis[2][1], semis[2][0], semis[2][2], semis[3][3], semis[3][1], semis[3][0],
         semis[3][2]])

    return jogos_semis_a, jogos_semis_b


def get_class_semis_seg_turno():
    jogos_semis_a, jogos_semis_b = semi_finais_seg_turno()
    semis_a = jogos_semis_a
    semis_b = jogos_semis_b

    dict_nomes = {}
    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

        for k, v in json.loads(nomes).items():
            dict_nomes[k] = v

    finais_a = {}
    for item in semis_a:
        if item[2] in finais_a or item[6] in finais_a:
            finais_a[item[2]].append([item[0], item[3]])
            finais_a[item[6]].append([item[4], item[7]])
        else:
            finais_a[item[2]] = [item[0], item[3]]
            finais_a[item[6]] = [item[4], item[7]]

    finais_b = {}
    for item in semis_b:
        if item[2] in finais_b or item[6] in finais_b:
            finais_b[item[2]].append([item[0], item[3]])
            finais_b[item[6]].append([item[4], item[7]])
        else:
            finais_b[item[2]] = [item[0], item[3]]
            finais_b[item[6]] = [item[4], item[7]]

    times_finais_a = []
    for key, value in finais_a.items():
        times_finais_a.append([key, value])

    times_finais_b = []
    for key, value in finais_b.items():
        times_finais_b.append([key, value])

    data1 = sorted(times_finais_a[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)
    data2 = sorted(times_finais_b[0:2], key=lambda x: (x[1][0] + x[1][1], x[1][0] + x[1][1]), reverse=True)

    semis = [data1[0][0], data2[0][0]]

    list_finais = []
    for x in range(len(semis)):
        for ids, nomes in dict_nomes.items():
            if semis[x] in nomes:
                list_finais.append(ids)

    return list_finais


def finais_seg_turno():
    dict_finais_ = collections.defaultdict(list)
    dict_finais_pts = {}
    ordered_dict_finais = {}
    finais = []
    dict_matamata_finais = {}

    with open('static/dict_matamata.json', encoding='utf-8', mode='r') as currentFile:
        data_matamata = currentFile.read().replace('\n', '')

        for x, y in json.loads(data_matamata).items():
            dict_matamata_finais[x] = y

    if len(dict_matamata_finais['finais']) == 0:
        dict_matamata['finais'] = get_class_semis_seg_turno()

        with open(f'static/dict_matamata.json', 'w') as f:
            json.dump(dict_matamata, f)

        list_finais_seg_turno = dict_matamata['finais']

    else:
        list_finais_seg_turno = dict_matamata_finais['finais']

    with open('static/escudos.json', encoding='utf-8', mode='r') as currentFile:
        escudos = currentFile.read().replace('\n', '')

    with open('static/nomes.json', encoding='utf-8', mode='r') as currentFile:
        nomes = currentFile.read().replace('\n', '')

    for rod_finais in rodadas_finais_seg_turno:

        if str(rod_finais) in get_times_rodada():
            for key, v in get_times_rodada()['1'].items():
                adict = get_times_rodada()[str(rod_finais)]
                dict_finais_[key].append(adict[key])

        else:
            for key, v in get_times_rodada()['1'].items():
                dict_finais_[key].append(0.00)

    novo_dict_finais = dict(dict_finais_)

    for time_id in list(novo_dict_finais):
        if time_id not in list_finais_seg_turno:
            novo_dict_finais.pop(str(time_id))

    for item in list_finais_seg_turno:
        ordered_dict_finais[str(item)] = novo_dict_finais[str(item)]

    for chave, valor in ordered_dict_finais.items():
        for c, v in json.loads(escudos).items():
            for id, nome in json.loads(nomes).items():
                if chave == c:
                    if chave == id:
                        dict_finais_pts[nome] = [v, valor]

    if api.mercado().status.nome == 'Mercado fechado':
        with ThreadPoolExecutor(max_workers=40) as executor:
            threads = executor.map(api.time_parcial, list_finais_seg_turno)
            # threads = executor.map(get_parciais, list_oitavas_seg_turno)

        for teams in threads:
            dict_finais_pts[teams.info.nome][1].append(teams.pontos)

    for key, value in dict_finais_pts.items():
        finais.append([key,
                       value[0],
                       value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 37 else value[1][0],
                       value[1][2] if api.mercado().status.nome == 'Mercado fechado' and rod == 38 else value[1][1]]
                      )

    jogos_final_a = []
    jogos_final_a.append(
        [finais[0][2], finais[0][1], finais[0][0], finais[0][3]])

    jogos_final_b = []
    jogos_final_b.append(
        [finais[1][3], finais[1][1], finais[1][0], finais[1][2]])

    esq_maior = False
    if jogos_final_a[0][0] + jogos_final_a[0][3] > jogos_final_b[0][0] + jogos_final_b[0][3]:
        esq_maior = True

    return jogos_final_a, jogos_final_b, esq_maior


def mata_mata_seg_turno():
    jogos_oitavas_a, jogos_oitavas_b = oitavas_de_final_seg_turno()
    jogos_quartas_a, jogos_quartas_b = quartas_de_final_seg_turno()
    jogos_semis_a, jogos_semis_b = semi_finais_seg_turno()
    jogos_final_a, jogos_final_b, esq_maior = finais_seg_turno()
    campeao_prim_turno = ''
    vice_prim_turno = ''

    for f_a, f_b in zip(jogos_final_a, jogos_final_b):
        if f_a[0] + f_a[3] > f_b[3] + f_b[0]:
            campeao_prim_turno = f_a[2]
            vice_prim_turno = f_b[2]
        else:
            campeao_prim_turno = f_b[2]
            vice_prim_turno = f_a[2]

    dict_prem['liberta_seg_turno']['campeao'] = campeao_prim_turno
    dict_prem['liberta_seg_turno']['vice'] = vice_prim_turno

    with open(f'static/dict_prem.json', 'w', encoding='utf-8') as f:
        json.dump(dict_prem, f)

    # print(jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, jogos_final_a, jogos_final_b, esq_maior)
    # return jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, jogos_final_a, jogos_final_b
    return jogos_oitavas_a, jogos_oitavas_b, jogos_quartas_a, jogos_quartas_b, jogos_semis_a, jogos_semis_b, jogos_final_a, jogos_final_b, esq_maior


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
