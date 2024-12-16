import sys
import os
import cv2

original_dir = os.getcwd()
sys.path.insert(0, original_dir + "/Detic/third_party/CenterNet2/")
sys.path.insert(0, original_dir + "/Detic/")
os.chdir(os.path.join(original_dir, "Detic"))


from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

# Add the necessary paths
sys.path.insert(0, 'third_party/CenterNet2/')
from centernet.config import add_centernet_config
from detic.config import add_detic_config
from detic.modeling.utils import reset_cls_test
from detic.modeling.text.text_encoder import build_text_encoder

os.chdir(original_dir)

class DeticDetector:
    def __init__(self, vocabulary=['cardboard box'], device='cpu'):
        os.chdir(os.path.join(original_dir, "Detic"))
        self.cfg = self._setup_cfg(device)
        self.predictor = DefaultPredictor(self.cfg)
        self.metadata = self._setup_metadata(vocabulary)
        self._setup_classifier(vocabulary)
        self.vocabulary = vocabulary
        os.chdir(original_dir)


    def _setup_cfg(self, device):
        cfg = get_cfg()
        add_centernet_config(cfg)
        add_detic_config(cfg)
        cfg.merge_from_file("configs/Detic_LCOCOI21k_CLIP_SwinB_896b32_4x_ft4x_max-size.yaml")
        cfg.MODEL.WEIGHTS = 'https://dl.fbaipublicfiles.com/detic/Detic_LCOCOI21k_CLIP_SwinB_896b32_4x_ft4x_max-size.pth'
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        cfg.MODEL.ROI_BOX_HEAD.ZEROSHOT_WEIGHT_PATH = 'rand'
        cfg.MODEL.ROI_HEADS.ONE_CLASS_PER_PROPOSAL = True
        cfg.MODEL.DEVICE = device
        return cfg

    def _setup_metadata(self, vocabulary):
        metadata = MetadataCatalog.get("__unused")
        metadata.thing_classes = vocabulary
        return metadata

    def _setup_classifier(self, vocabulary):
        classifier = self._get_clip_embeddings(vocabulary)
        num_classes = len(vocabulary)
        reset_cls_test(self.predictor.model, classifier, num_classes)
        output_score_threshold = 0.3
        for cascade_stages in range(len(self.predictor.model.roi_heads.box_predictor)):
            self.predictor.model.roi_heads.box_predictor[cascade_stages].test_score_thresh = output_score_threshold

    def _get_clip_embeddings(self, vocabulary, prompt='a '):
        text_encoder = build_text_encoder(pretrain=True)
        text_encoder.eval()
        texts = [prompt + x for x in vocabulary]
        emb = text_encoder(texts).detach().permute(1, 0).contiguous().cpu()
        return emb

    def detect(self, image_path):
        image = cv2.imread(image_path)
        outputs = self.predictor(image)
        
        instances = outputs["instances"].to("cpu")
        boxes = instances.pred_boxes.tensor.numpy()
        scores = instances.scores.numpy()
        class_ids = instances.pred_classes.numpy()
        
        # Convert boxes to COCO format (x_center, y_center, width, height)
        image_height, image_width = image.shape[:2]
        coco_boxes = []
        for box in boxes:
            x1, y1, x2, y2 = box
            x_center = (x1 + x2) / (2 * image_width)
            y_center = (y1 + y2) / (2 * image_height)
            width = (x2 - x1) / image_width
            height = (y2 - y1) / image_height
            coco_boxes.append((x_center, y_center, width, height))
        
        # Convert class IDs to label strings
        labels = [self.vocabulary[class_id] for class_id in class_ids]
        
        return coco_boxes, labels, scores.tolist()

    def visualize(self, image_path, output_path):
        image = cv2.imread(image_path)
        outputs = self.predictor(image)
        v = Visualizer(image[:, :, ::-1], self.metadata)
        out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        cv2.imwrite(output_path, out.get_image()[:, :, ::-1])