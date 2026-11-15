import sys, json, os
OUT = sys.argv[1]; MARGV = int(sys.argv[2]); SIZE = int(sys.argv[3]); PH = int(sys.argv[4])
tl = json.load(open(os.path.join(OUT, "tl.json")))
CAP = [(0,1.45,"Vos clients vous cherchent {en ligne}…"),(1.92,3.37,"et ils trouvent vos {concurrents.}"),
(3.83,4.80,"Restez jusqu'à la fin :"),(5.12,6.87,"on vous montre comment avoir votre site…"),(7.18,8.49,"et le payer en {3 fois.}"),
(8.97,9.85,"{Restaurant,}"),(9.92,10.55,"{boutique,}"),(10.63,11.1,"{école,}"),(11.15,11.64,"{média,}"),(11.73,12.46,"{entreprise,}"),
(12.55,13.16,"{événement,}"),(13.24,14.0,"{institution,}"),(14.01,14.55,"{clinique…}"),
(14.90,16.99,"Chaque activité a besoin de {son site.}"),(17.30,18.26,"Ou de {son application.}"),
(18.64,20.02,"Nous avons même créé {Kibaa,}"),(20.20,23.38,"notre propre application de messagerie, disponible sur {Google Play.}"),
(23.81,24.68,"Alors votre projet ?"),(25.06,25.70,"{On sait le faire.}"),
(26.12,28.55,"Un site professionnel à partir de {50 000 F.}"),(28.82,30.60,"Livré en {1 semaine à 1 mois.}"),
(30.92,32.88,"Un {entretien} pour comprendre votre activité."),(33.15,35.19,"Un {cahier des charges} validé ensemble."),
(35.48,36.89,"Une {maquette} avant de commencer."),(37.41,39.32,"Et toute {l'équipe} mobilisée sur votre projet."),
(39.67,40.12,"Et le paiement ?"),(40.42,41.71,"{50 %} au lancement,"),(41.97,42.91,"{30 %} à la livraison…"),
(43.18,45.48,"et les {20 derniers} après 30 jours d'utilisation."),(45.78,47.46,"Vous payez le reste {quand ça marche.}"),
(47.79,48.85,"Ils nous ont fait confiance."),(49.17,49.92,"La prochaine case…"),(50.26,50.74,"c'est {la vôtre ?}"),
(51.10,52.10,"Écrivez-nous sur {WhatsApp.}"),(52.55,53.95,"Et la prochaine fois qu'on vous cherche…"),(54.28,54.87,"{on vous trouve.}")]
def colorize(tx):
    out=""; i=0
    while i<len(tx):
        if tx[i]=="{":
            j=tx.index("}",i); out+="{\\c&H1991FF&}"+tx[i+1:j]+"{\\c&HFFFFFF&}"; i=j+1
        else: out+=tx[i]; i+=1
    return out
def at(t): return "%d:%02d:%05.2f"%(t//3600,t%3600//60,t%60)

OFF = []; o = 0.0
for a, b in tl["segs"]: OFF.append((a, b, o)); o += b - a
L=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: %d" % PH,"WrapStyle: 0","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Cap,Inter Display ExtraBold,%d,&H00FFFFFF,&H00FFFFFF,&H00B42E06,&H64000000,0,0,0,0,100,100,0,0,1,7,2,2,70,70,%d,1" % (SIZE, MARGV),"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for s0, s1, tx in CAP:
    for a, b, o in OFF:
        if s1 <= a or s0 >= b: continue
        st = o + max(s0, a) - a; en = o + min(s1 + .2, b) - a
        L.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,{\\fad(50,50)\\fscx90\\fscy90\\t(0,130,\\fscx100\\fscy100)}%s" % (at(st), at(en), colorize(tx)))
open(os.path.join(OUT, "caps.ass"), "w").write("\n".join(L) + "\n")
