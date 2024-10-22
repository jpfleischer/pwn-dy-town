# pwn-dy-town

ideas 
    make a random offset timer to stand and resit pony during intervals of 1 - 14mins 
        2 - sit 
        3 - stand 
        O - zoom out 
        p - zoom in 

get ALT cookies instead of main
    dress up ALT in some random fandom outfit 
    hotline miami 

sit in certain groups at 2x zoom to capture individual group conversations 
    (try to blend in?!?!?!?!?!?!)


## Requirements

WSL
make a env3 on wsl

```bash
python -m venv ~/ENV3
source ~/ENV3/bin/activate
pip install -r requirements.txt
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev

sudo add-apt-repository ppa:alex-p/tesseract-ocr5
sudo apt update
sudo apt install tesseract-ocr

#sudo wget https://github.com/tesseract-ocr/tessdata/raw/refs/heads/main/eng.traineddata -P /usr/share/tesseract-ocr/5/tessdata/
sudo cp eng* /usr/share/tesseract-ocr/5/tessdata/.
```

## Actual use

```bash
python themainone.py
# now we have some logs
# get coordinates of logs using AI
python combined.py
```