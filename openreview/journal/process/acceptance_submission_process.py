def process(client, edit, invitation):

    note = client.get_note(edit.note.id)

    journal = openreview.journal.Journal()
