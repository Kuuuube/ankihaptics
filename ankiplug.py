from aqt import gui_hooks

def answer_button_press(reviewer, card, ease):
    print(ease)

def register_hooks():
    gui_hooks.reviewer_did_answer_card.append(answer_button_press)
