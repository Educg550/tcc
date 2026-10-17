"""Executado no runtime original, com fixtures declarativas injetadas por ambiente.py."""
import json
import psycopg
from psycopg.rows import dict_row

forms = psycopg.connect("host=db dbname=caronte_forms user=caronte_admin password=caronte_admin", row_factory=dict_row)
prejanus = psycopg.connect("host=db dbname=caronte_prejanus user=caronte_admin password=caronte_admin", row_factory=dict_row)
with forms, prejanus:
    prejanus.execute(FIXTURE_USUARIOS)
    prejanus.execute(FIXTURE_PREJANUS)
    forms.execute(FIXTURE_CONSULTA)
    prejanus.execute(FIXTURE_INSCRICAO)
    usuarios = [
        (1, "Admin Piloto", "admin.piloto@example.com", "administrator"),
        (2, "Docente Piloto", "docente.piloto@example.com", "teacher"),
        (3, "Outra Docente", "outra.piloto@example.com", "teacher"),
        (4, "Secretaria Piloto", "secretaria.piloto@example.com", "secretary"),
        (5, "Coordenador Piloto", "coordenador.piloto@example.com", "coordinator"),
        (6, "Estudante Piloto", "estudante.piloto@example.com", "student"),
    ]
    for id, nome, email, papel in usuarios:
        prejanus.execute('UPDATE "user" SET name=%s,email=%s,nusp=%s,role=%s WHERE id=%s',
                         (nome, email, f"90000{id}", papel, id))
        prejanus.execute('INSERT INTO "user"(id,name,email,nusp,role) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',
                         (id,nome,email,f"90000{id}",papel))
    prejanus.execute("UPDATE edict SET accept_forms='4',phase='avaliacao' WHERE id=1")
    prejanus.execute("INSERT INTO edict(id,title,description,candidate_forms,recommenders_forms,accept_forms,closed_date,year,semester,type,phase,is_open,user_id) "
                     "VALUES(2,'Piloto v2 - Doutorado','Edital doutorado','3','2','4','2030-04-01',2026,2,'doutorado','avaliacao',true,1)")
    prejanus.execute("INSERT INTO edict_phase(id,edict_id,phase,closed_date) SELECT id+4,2,phase,closed_date FROM edict_phase WHERE edict_id=1")
    forms.execute("""INSERT INTO form_section SELECT (jsonb_populate_record(NULL::form_section,
        to_jsonb(s)||jsonb_build_object('id',s.id+100,'version',2,'is_active',true))).*
        FROM form_section s WHERE form_id=1""")
    forms.execute("UPDATE form_field SET is_active=false WHERE form_id=1 AND id<1000")
    forms.execute("""INSERT INTO form_field SELECT (jsonb_populate_record(NULL::form_field,
        to_jsonb(f)||jsonb_build_object('id',f.id+1000,'section_id',f.section_id+100,'version',2,'is_active',true))).*
        FROM form_field f WHERE form_id=1""")
    forms.execute("""INSERT INTO field_option SELECT (jsonb_populate_record(NULL::field_option,
        to_jsonb(o)||jsonb_build_object('id',o.id+10000,'field_id',o.field_id+1000))).*
        FROM field_option o JOIN form_field f ON f.id=o.field_id WHERE f.form_id=1 AND f.id<1000""")
    forms.execute("UPDATE form_section SET is_active=false WHERE form_id=1 AND id<100")
    forms.execute("UPDATE form_field SET is_active=false WHERE form_id=1 AND id<1000")
    forms.execute("UPDATE form SET version=2 WHERE id=1")
    forms.execute("""INSERT INTO form_response(id,form_id,shared_id,email,token,current_section,submitted_at,metadata,form_version)
        VALUES(2,1,1,'bruno.piloto@example.com','c0a5e1f0-0000-4000-8000-000000000002',8,'2026-10-17 12:00:00','{}',2)""")
    forms.execute("INSERT INTO responses(response_id,field_id,value) SELECT 2,field_id+1000,CASE "
                  "WHEN field_id=2 THEN 'Bruno Piloto V2' WHEN field_id=35 THEN 'recomendador.bruno@example.com' "
                  "ELSE value END FROM responses WHERE response_id=1")
    forms.execute("UPDATE responses r SET value=lpad(to_hex(2000+f.id),32,'0')||'_'||f.name||'.pdf' "
                  "FROM form_field f WHERE r.response_id=2 AND r.field_id=f.id AND f.type='File'")
    prejanus.execute("INSERT INTO submission(id,edict_id,candidate_form_id,candidate_form_version,recommender_form_version,stats,letter_sent) "
                     "VALUES(2,1,2,2,1,'underreview',false)")
    mapping = prejanus.execute("SELECT mapping FROM edict_form_mappings WHERE id=1").fetchone()["mapping"]
    def versao2(node):
        if isinstance(node,dict) and "section" in node and "field" in node:
            return {"section":node["section"]+100,"field":node["field"]+1000}
        return {k:versao2(v) for k,v in node.items()} if isinstance(node,dict) else node
    prejanus.execute("INSERT INTO edict_form_mappings(edict_id,form_id,form_type,form_version,mapping,user_id,is_active) "
                     "VALUES(1,'1','candidate',2,%s,1,true)",(json.dumps(versao2(mapping)),))
    fields = forms.execute("SELECT * FROM form_field WHERE form_id=3 ORDER BY id").fetchall()
    forms.execute("INSERT INTO form_shared(id,form_id,token,unique_answers,is_public,expiration_at,created_at) "
                  "VALUES(3,3,'c0a5e1f0-0000-4000-8000-000000000003',false,true,'2030-04-01',now())")
    forms.execute("INSERT INTO form_response(id,form_id,shared_id,email,token,current_section,submitted_at,metadata,form_version) "
                  "VALUES(3,3,3,'carla.piloto@example.com','c0a5e1f0-0000-4000-8000-000000000003',10,'2026-10-17 13:00:00','{}',1)")
    conhecidos = {"fullname":"Carla Doutorado V2","birth":"1997-06-20","birth-date":"1997-06-20",
                  "biological-sex":"Feminino","nationality":"Brasileira","phone-number":"+55 11 99999-0003",
                  "grades-poscomp":"","year-poscomp":"2025","year-of-graduation":"2021","scholarship":"Sim"}
    valores = {}
    for f in fields:
        valor = conhecidos.get(f["name"], "")
        if f["type"] == "File": valor=f"{3000+f['id']:032x}_{f['name']}.pdf"
        elif f["type"] == "CheckBox": valor='[]'
        elif f["type"] == "Date": valor="1997-06-20"
        elif f["type"] == "Number" and f["name"] not in conhecidos: valor="2021"
        elif f["name"] not in conhecidos: valor=f"Fixture doutorado: {f['name']}"
        valores[f["name"]] = valor
        forms.execute("INSERT INTO responses(response_id,field_id,value) VALUES(3,%s,%s)",(f["id"],valor))
    lookup={f["name"]:{"section":f["section_id"],"field":f["id"]} for f in fields}
    def remap(node):
        if isinstance(node,dict) and "section" in node and "field" in node:
            old = forms.execute("SELECT name FROM form_field WHERE id=%s",(node["field"],)).fetchone()
            return lookup.get(old["name"])
        return {k:remap(v) for k,v in node.items()} if isinstance(node,dict) else node
    phdmap=remap(mapping)
    prejanus.execute("INSERT INTO edict_form_mappings(edict_id,form_id,form_type,form_version,mapping,user_id,is_active) "
                     "VALUES(2,'3','candidate',1,%s,1,true)",(json.dumps(phdmap),))
    prejanus.execute("INSERT INTO submission(id,edict_id,candidate_form_id,candidate_form_version,recommender_form_version,stats,letter_sent) "
                     "VALUES(3,2,3,1,1,'underreview',false)")
    forms.execute("INSERT INTO form_shared(id,form_id,token,unique_answers,is_public,expiration_at,created_at) "
                  "VALUES(4,2,'c0a5e1f0-0000-4000-8000-000000000004',false,true,'2030-04-01',now())")
    campos_rec = {f["name"]: f["id"] for f in forms.execute("SELECT id,name FROM form_field WHERE form_id=2").fetchall()}
    recomendacoes = [
        (4, "recomendadora.um@example.com", "Ana Piloto Caronte", "Paula Recomendadora Um", "IME-USP", "3 anos", "Paula recomenda a Ana."),
        (5, "recomendador.dois@example.com", "Ana Piloto Caronte", "Pedro Recomendador Dois", "UFABC", "1 ano", "Pedro recomenda a Ana."),
        (6, "recomendador.bruno@example.com", "Bruno Piloto V2", "Rui Recomendador Bruno", "Mackenzie", "2 anos", "Rui recomenda o Bruno."),
    ]
    for id, email, candidato, nome, afiliacao, tempo, texto in recomendacoes:
        forms.execute("INSERT INTO form_response(id,form_id,shared_id,email,token,current_section,submitted_at,metadata,form_version) "
                      "VALUES(%s,2,4,%s,%s,2,'2026-10-17 14:00:00','{}',1)", (id, email, f"c0a5e1f0-0000-4000-8000-0000000000{id:02d}"))
        valores_rec = {"fullname-candidate": candidato, "fullname": nome, "affiliation": afiliacao, "known-time": tempo,
                       "relationship": '["Ministrante de disciplina."]', "rating": texto}
        for campo, valor in valores_rec.items():
            forms.execute("INSERT INTO responses(response_id,field_id,value) VALUES(%s,%s,%s)", (id, campos_rec[campo], valor))
    # Nota do POSCOMP preenchida: o detalhe original falha (ver avaliacao.md).
    forms.execute("""INSERT INTO form_response(id,form_id,shared_id,email,token,current_section,submitted_at,metadata,form_version)
        VALUES(7,1,1,'diego.piloto@example.com','c0a5e1f0-0000-4000-8000-000000000007',8,'2026-10-17 15:00:00','{}',2)""")
    forms.execute("INSERT INTO responses(response_id,field_id,value) SELECT 7,r.field_id,CASE f.name "
                  "WHEN 'fullname' THEN 'Diego Poscomp V2' WHEN 'grades-poscomp' THEN '650' "
                  "WHEN 'recommended-email-1' THEN 'ninguem.diego@example.com' "
                  "WHEN 'semester' THEN 'Segundo semestre.' "
                  "ELSE CASE WHEN f.type='File' THEN lpad(to_hex(7000+f.id),32,'0')||'_'||f.name||'.pdf' ELSE r.value END END "
                  "FROM responses r JOIN form_field f ON f.id=r.field_id WHERE r.response_id=2")
    prejanus.execute("INSERT INTO submission(id,edict_id,candidate_form_id,candidate_form_version,recommender_form_version,stats,letter_sent) "
                     "VALUES(4,1,7,2,1,'underreview',false)")
    # Edital com PPI mapeado: a listagem original falha (ver avaliacao.md).
    prejanus.execute("INSERT INTO edict(id,title,description,candidate_forms,recommenders_forms,accept_forms,closed_date,year,semester,type,phase,is_open,user_id) "
                     "SELECT 3,'Piloto v2 - Mestrado PPI','Edital com PPI mapeado',candidate_forms,recommenders_forms,accept_forms,closed_date,year,semester,type,phase,is_open,user_id FROM edict WHERE id=1")
    prejanus.execute("INSERT INTO edict_phase(id,edict_id,phase,closed_date) SELECT id+8,3,phase,closed_date FROM edict_phase WHERE edict_id=1")
    prejanus.execute("""INSERT INTO edict_form_mappings(edict_id,form_id,form_type,form_version,mapping,user_id,is_active)
        SELECT 3,form_id,form_type,form_version,CASE WHEN form_type='candidate' THEN mapping||jsonb_build_object('ethnicity-race',
            jsonb_build_object('section',CASE form_version WHEN 1 THEN 2 ELSE 102 END,'field',CASE form_version WHEN 1 THEN 17 ELSE 1017 END))
            ELSE mapping END,user_id,is_active FROM edict_form_mappings WHERE edict_id=1""")
    prejanus.execute("INSERT INTO submission(id,edict_id,candidate_form_id,candidate_form_version,recommender_form_version,stats,letter_sent) "
                     "SELECT id+4,3,candidate_form_id,candidate_form_version,recommender_form_version,stats,letter_sent FROM submission WHERE edict_id=1")
    for conn, tabelas in ((forms,["form","form_shared","form_response","form_section","form_field","field_option","responses"]),
                          (prejanus,["user","edict","edict_phase","edict_form_mappings","submission"])):
        for tabela in tabelas:
            conn.execute(f"""SELECT setval(pg_get_serial_sequence('"{tabela}"','id'),(SELECT max(id) FROM "{tabela}"))""")
print("Fixture v2 criada: quatro formulários, duas versões de mestrado, quatro candidaturas, três recomendações, três editais e seis papéis.")
