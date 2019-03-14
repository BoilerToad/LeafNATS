'''
@author Tian Shi
Please contact tshi@vt.edu
'''
import torch
from torch.autograd import Variable

from LeafNATS.playground.multiTaskClassification.modelMTC_base import modelMTCBase
from LeafNATS.data.MultiTaskClassification.process_minibatch_v1 import process_minibatch
from LeafNATS.utils.utils import *

from LeafNATS.modules.encoder.encoder_rnn import EncoderRNN
'''
pointer generator network
''' 
class modelMTATTN(modelMTCBase):
    
    def __init__(self, args):
        super(modelMTATTN, self).__init__(args=args)
            
    def build_models(self):
        '''
        build all models.
        in this model source and target share embeddings
        '''
        self.train_models['embedding'] = torch.nn.Embedding(
            self.batch_data['vocab_size'], self.args.emb_dim
        ).to(self.args.device)
        torch.nn.init.uniform_(self.train_models['embedding'].weight, -1.0, 1.0)
        
        self.train_models['encoder'] = EncoderRNN(
            emb_dim = self.args.emb_dim,
            hidden_size = self.args.rnn_hidden_dim,
            nLayers = self.args.rnn_nLayers,
            rnn_network = self.args.rnn_network,
            device = self.args.device
        ).to(self.args.device)
        
        self.train_models['attn_forward'] = torch.nn.ModuleList(
            [torch.nn.Linear(self.args.rnn_hidden_dim*2, self.args.rnn_hidden_dim, bias=False) 
             for k in range(self.args.n_tasks)]).to(self.args.device)
        self.train_models['attn_wrap'] = torch.nn.ModuleList(
            [torch.nn.Linear(self.args.rnn_hidden_dim, 1, bias=False) 
             for k in range(self.args.n_tasks)]).to(self.args.device)
        
        self.train_models['classifier'] = torch.nn.ModuleList(
            [torch.nn.Linear(2*self.args.rnn_hidden_dim, self.args.n_class)
             for k in range(self.args.n_tasks)]).to(self.args.device)
        
        self.loss_criterion = torch.nn.CrossEntropyLoss().to(self.args.device)
                        
    def build_batch(self, batch_):
        '''
        get batch data
        '''
        review, weight_mask, rating, features = process_minibatch(
            input_=batch_,
            vocab2id=self.batch_data['vocab2id'],
            max_lens=self.args.review_max_lens
        )
        self.batch_data['review'] = review.to(self.args.device)
        self.batch_data['weight_mask'] = weight_mask.to(self.args.device)
        self.batch_data['rating'] = rating.to(self.args.device)
        
    def build_pipe(self):
        '''
        Shared pipe
        '''
        review_emb = self.train_models['embedding'](self.batch_data['review'])
        batch_size = review_emb.size(0)
        encoder_hy, hidden_ = self.train_models['encoder'](review_emb)
        logits = []
        for k in range(self.args.n_tasks):
            attn = torch.tanh(self.train_models['attn_forward'][k](encoder_hy))
            attn = self.train_models['attn_wrap'][k](attn).squeeze(2)
            attn = torch.softmax(attn, 1)
        
            cv_hidden = torch.tanh(torch.bmm(attn.unsqueeze(1), encoder_hy).squeeze(1))
            logits.append(self.train_models['classifier'][k](cv_hidden))
        
        logits = torch.cat(logits, 0)
        logits = logits.view(self.args.n_tasks, batch_size, self.args.n_class)
        logits = logits.transpose(0, 1)
                
        return logits
        
    def build_pipelines(self):
        '''
        here we have all data flow from the input to output
        '''
        logits = self.build_pipe()
        logits = logits.contiguous().view(-1, self.args.n_class)
                
        loss = self.loss_criterion(logits, self.batch_data['rating'].view(-1))

        return loss
    
    def test_worker(self):
        '''
        For the testing.
        '''
        logits = self.build_pipe()
        logits = torch.softmax(logits, dim=2)
        
        ratePred = logits.topk(1, dim=2)[1].squeeze(2).data.cpu().numpy()
        ratePred += 1
        ratePred = ratePred.tolist()
        
        rateTrue = self.batch_data['rating'].data.cpu().numpy()
        rateTrue += 1
        rateTrue = rateTrue.tolist()
        
        return ratePred, rateTrue