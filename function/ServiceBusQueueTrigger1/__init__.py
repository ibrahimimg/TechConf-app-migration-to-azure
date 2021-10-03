import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    #return notification_id
    logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)

    # Get connection to database
    dbname="techconfdb"
    user="azureuser@ud3server"
    password="ud3server@AZURE"
    host="ud3server.postgres.database.azure.com"

    cs =  "dbname=%s user=%s password=%s host=%s port='5432' sslmode='require'" % (dbname,user,password,host)
    try:
        cs = os.environ['dbConnection']
    except:
        pass
    conn = psycopg2.connect(cs)
    cur = conn.cursor()
    try:
        # Get notification message and subject from database using the notification_id
        get_notification_query = "SELECT message, subject FROM notification WHERE id = %d;"%(notification_id,)
        get_notification_result = cur.execute(get_notification_query)
        notification = cur.fetchone()

        # Get attendees email and name
        get_attendees_query = "SELECT email, first_name FROM attendee;"
        cur.execute(get_attendees_query)
        attendees = cur.fetchall()

                
        # Loop through each attendee and send an email with a personalized subject
        attendees_notified = 0
        for attendee in attendees:
            Mail(
                from_email='info@techconf.com',
                to_emails=attendee[0],
                subject=notification[1],
                plain_text_content=notification[0]
            )

            attendees_notified += 1
        
        # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        completed_date = datetime.utcnow()
        notification_status = 'Notified {} attendees'.format(attendees_notified)
        notification_update_query = f"UPDATE notification SET status = '{notification_status}', completed_date = '{completed_date}' WHERE id={notification_id};"
        cur.execute(notification_update_query)
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # Close connection
        conn.close()
