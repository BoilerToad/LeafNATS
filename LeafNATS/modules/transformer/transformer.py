'''
@author Tian Shi
Please contact tshi@vt.edu

https://github.com/codertimo/BERT-pytorch.git
https://github.com/namisan/mt-dnn
https://github.com/dhlee347/pytorchic-bert.git
'''
import math
import torch

from LeafNATS.modules.attention.attention_multi_head import MultiHeadedAttention
from .utils import *

class TransformerBlock(torch.nn.Module):
    '''
    Implementation of Transformer
    '''
    def __init__(
        self, 
        hidden_size, 
        n_heads, 
        ff_size, 
        drop_rate
    ):
        super(TransformerBlock, self).__init__()
        # multi-head attention
        self.attentionMH = MultiHeadedAttention(n_heads, hidden_size, drop_rate)
        # layer normalization
        self.norm1 = LayerNormalization(hidden_size)
        self.norm2 = LayerNormalization(hidden_size)
        # layer feed-forward
        self.layer_ff = PositionwiseFeedForward(hidden_size, ff_size, drop_rate)
        
        self.drop = torch.nn.Dropout(drop_rate)

    def forward(self, input_, mask=None):
        '''
        Transformer
        '''
        hd = self.attentionMH(input_, mask)
        hd = self.norm1(input_ + self.drop(hd))
        hd = self.norm2(hd + self.layer_ff(hd))

        return self.drop(hd)

    
    
    