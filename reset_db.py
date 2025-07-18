from main import app, db, ChatHistory

with app.app_context():
    db.session.query(ChatHistory).delete()
    db.session.commit()
    print("✅ ChatHistory table ka sara data delete ho gaya.")
