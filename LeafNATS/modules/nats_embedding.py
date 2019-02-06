'''
@author Tian Shi
Please contact tshi@vt.edu
'''
import torch
from torch.autograd import Variable

class natsEmbedding(torch.nn.Module):
    
    def __init__(
        self,
        vocab_size, # vocab size
        emb_dim, # embedding dimension
        share_emb_weight
    ):
        '''
        embedding and decoding.
        '''
        super(natsEmbedding, self).__init__()
        
        self.embedding = torch.nn.Embedding(
            vocab_size, emb_dim)
        torch.nn.init.uniform_(self.embedding.weight, -1.0, 1.0)
        
        '''
        Only used in summarization
        '''
        if share_emb_weight:
            self.proj2vocab = torch.nn.Linear(
                emb_dim, vocab_size)
            self.proj2vocab.weight.data = self.embedding.weight.data

    def get_embedding(self, input_):
        '''
        get the embedding
        '''
        return self.embedding(input_)
    
    def get_decode2vocab(self, input_):
        '''
        from vector to vocab prediction
        '''
        return self.proj2vocab(input_)
    
    