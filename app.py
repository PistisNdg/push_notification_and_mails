from db import get_connection
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import smtplib
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import logging
import threading

load_dotenv()

# Logging de base
logging.basicConfig(level=logging.INFO)

# Replace ZoneInfo usage with pytz
API_KEY=os.getenv("API_KEY")
EMAIL=os.getenv("EMAIL")
PASS=os.getenv("PASS")

def is_authorized(req):
    return req.headers.get("x-api-key")==API_KEY

def send_notification(title, message):    
    firebase_service_account_json = os.getenv("FIREBASE_KEY")
    firebase_config = json.loads(firebase_service_account_json)
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
    # Construire le message
    message = messaging.Message(
        notification=messaging.Notification(
            title='Nouvelle Annonce !',
            body="Découvrez les dernières nouveautés de notre application. C'est génial !",
        ),
        # Le nom du sujet doit correspondre à celui auquel les clients s'abonnent
        topic='allUsers',
        # Vous pouvez ajouter des données personnalisées si nécessaire
    )

    # Envoyer le message
    try:
        response = messaging.send(message)
        logging.info('Message envoyé avec succès:', response)
    except Exception as e:
        logging.info(f'Erreur lors de l\'envoi du message: {e}')
    
def envoie_mail_to_all(titre, contenu):
    """Fonction pour envoyer des mails à tous les étudiants"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE statut='Etudiant'")
        rows = cursor.fetchall()
        conn.close()

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(EMAIL, PASS)

        for row in rows:
            to_ = row[0]
            subj = "Univ News : " + "Test"
            msg = f"Subject: {subj}\nContent-Type: text/plain; charset=utf-8\n\nPitié, faite que ça marche"
            s.sendmail(EMAIL, to_, msg.encode('utf-8'))
            logging.info(f"Mail envoyé à {to_}")

    except Exception as e:
        logging.info(f"Erreur d'envoi de mail : {str(e)}")
        return False
    
def verifier_et_envoyer():
    #logging.info("Démarrage du service de vérification des news")
    while True:
        try:
            conn = None
            cursor = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT newsid, datedepublication, titreapresvalidation, contenuapresvalidation 
                    FROM news 
                    WHERE statut='Validée (Programmé)'
                """)
                result = cursor.fetchall()
                current_date = time.strftime("%Y-%m-%d")
                for row in result:
                    newsid, date, titre, contenu = row
                    if date == current_date:
                        #logging.info(f"Traitement de la news {newsid} pour publication")
                        if envoie_mail_to_all(titre, contenu):
                            send_notification(titre, contenu)
                            cursor.execute("UPDATE news SET statut='Publiée' WHERE newsid=%s", (newsid,))
                            conn.commit()
                            #logging.info(f"News {newsid} publiée avec succès")
                        else:
                            logging.error(f"Échec de l'envoi des notifications pour la news {newsid}")
                
            except Exception as e:
                logging.error(f"Erreur lors de la vérification des news: {str(e)}")
                if conn and not conn.closed:
                    conn.rollback()
            
            finally:
                if cursor:
                    cursor.close()
                if conn and not conn.closed:
                    conn.close()
                    
            # Attendre 5 minutes avant la prochaine vérification
            time.sleep(300)
            
        except Exception as e:
            logging.error(f"Erreur critique dans la boucle principale: {str(e)}")
            # En cas d'erreur critique, attendre 1 minute avant de réessayer
            time.sleep(60)

# Lancer le vérificateur en parallèle du serveur Flask
threading.Thread(target=verifier_et_envoyer, daemon=True).start()
