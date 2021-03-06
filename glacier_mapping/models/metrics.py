#  metrics and losses
import torch


def precision(pred, true, label=1):
    tp = ((pred == label) & (true == label)).sum(dim=[0, 1, 2])
    fp = ((pred == label) & (true != label)).sum(dim=[0, 1, 2])

    result = torch.true_divide(tp, tp + fp)
    result[(tp == fp) & (fp == 0)] = 0

    return result


def tp_fp_fn(pred, true, label=1):
    tp = ((pred == label) & (true == label)).sum(dim=[0, 1, 2])
    fp = ((pred == label) & (true != label)).sum(dim=[0, 1, 2])
    fn = ((pred != label) & (true == label)).sum(dim=[0, 1, 2])

    return tp, fp, fn


def recall(pred, true, label=1):
    tp = ((pred == label) & (true == label)).sum(dim=[0, 1, 2])
    fn = ((pred != label) & (true == label)).sum(dim=[0, 1, 2])

    result = torch.true_divide(tp, tp + fn)
    result[(tp == fn) & (fn == 0)] = 0

    return result

def pixel_acc(pred, true):
    correct = (pred == true).sum(dim=[0, 1, 2])
    count = true.shape[0] * true.shape[1] * true.shape[2]
    return torch.true_divide(correct, count)


def dice(pred, true, label=1):
    tp = ((pred == label) & (true == label)).sum(dim=[0, 1, 2])
    fp = ((pred == label) & (true != label)).sum(dim=[0, 1, 2])
    fn = ((pred != label) & (true == label)).sum(dim=[0, 1, 2])

    return torch.true_divide(2 * tp, 2 * tp + fp + fn)


def IoU(pred, true, label=1):
    tp = ((pred == label) & (true == label)).sum(dim=[0, 1, 2])
    fp = ((pred == label) & (true != label)).sum(dim=[0, 1, 2])
    fn = ((pred != label) & (true == label)).sum(dim=[0, 1, 2])
    return torch.true_divide(tp, tp + fp + fn)


class diceloss(torch.nn.Module):
    def __init__(self, act=torch.nn.Sigmoid(), smooth=0, w=[1.0]):
        super().__init__()
        self.act = act
        self.smooth = smooth
        self.w = w

    def forward(self, pred, target):
        pred = self.act(pred)
        if len(pred.shape) > len(target.shape):
            target = torch.nn.functional.one_hot(target).permute(0, 3, 1, 2)

        intersection = (pred * target).sum(dim=[0, 2, 3])
        A_sum = (pred * pred).sum(dim=[0, 2, 3])
        B_sum = (target * target).sum(dim=[0, 2, 3])
        union = A_sum + B_sum

        dice = 1 - ((2.0 * intersection + self.smooth) / (union + self.smooth))
        dice = dice * torch.tensor(self.w).to(device=dice.device)

        return dice.sum()