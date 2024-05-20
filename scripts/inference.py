import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import numpy as np
import torch
import sentencepiece as spm
import argparse
from model.encoder import *
from model.decoder import *
from model.transformer import *



device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
num_layers = 4
num_heads = 4
d_model = 256
d_ff = 1024

encoder = Encoder(vocab_size=10000, n_layer=num_layers, n_head=num_heads, d_model=d_model, d_ff=d_ff)
decoder = Decoder(vocab_size=10000, n_layer=num_layers, n_head=num_heads, d_model=d_model, d_ff=d_ff)
model = EncoderDecoder(encoder, decoder, device).to(device)
model_path = os.path.join(parent_dir, 'checkpoints', 'model_epoch_11.pt')
model.load_state_dict(torch.load(model_path))

spm_model_path = os.path.join(parent_dir, 'data','spm', 'ten_zh_spm.model')
sp = spm.SentencePieceProcessor(model_file=spm_model_path)

def translate(src_sentence, model, sp, max_length=10):
    model.eval()

    # Tokenize the source sentence
    src_tokens = sp.encode_as_ids(src_sentence)
    src_tensor = torch.LongTensor(src_tokens).unsqueeze(0).to(device)

    with torch.no_grad():
        src_mask = model.padding_mask(src_tensor)
        memory = model.encoder(src_tensor, src_mask)

    trg_indexes = [sp.bos_id()]
    for _ in range(max_length):
        trg_tensor = torch.LongTensor(trg_indexes).unsqueeze(0).to(device)
        trg_mask = model.target_mask(trg_tensor)

        with torch.no_grad():
            output = model.decoder(trg_tensor, memory, src_mask, trg_mask)
            pred_token = output.argmax(2)[:, -1].item()
            trg_indexes.append(pred_token)

        if pred_token == sp.eos_id():
            break

    trg_tokens = sp.decode_ids(trg_indexes)
    return trg_tokens.replace(" ", "")

def main():
    parser = argparse.ArgumentParser(description='Translate an English sentence to Chinese.')
    parser.add_argument('sentence', type=str, help='The English sentence to translate.')
    args = parser.parse_args()

    src_sentence = args.sentence

    if not isinstance(src_sentence, str):
        raise TypeError("Input sentence must be a string.")
    
    if not src_sentence.strip():
        raise ValueError("Input sentence cannot be empty or whitespace.")

    translated_sentence = translate(src_sentence, model, sp)
    print("Translated Sentence:", translated_sentence)

if __name__ == '__main__':
    main()