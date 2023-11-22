from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import math

class Visualizer:
    def __init__(self):
        # 初始化

        # 颜色相关设置
        # type colors控制着不同类型所对应的颜色, 默认设置30个颜色, 如果需要重新配置可以使用set type colors函数
        self.type_colors = {'0': (205, 0, 205), \
                  '1': (205, 198, 115), \
                  '2': (255, 215, 0), \
                  '3': (205, 173, 0), \
                  '4': (238, 180, 34), \
                  '5': (205, 155, 155), \
                  '6': (238, 99, 99), \
                  '7': (205, 85, 85), \
                  '8': (139, 58, 58), \
                  '9': (238, 121, 66), \
                  '10':(205, 104, 57), \
                  '11':(205, 170, 125), \
                  '12':(238, 154, 73), \
                  '13':(255, 127, 36), \
                  '14':(255, 48, 48), \
                  '15':(205, 38, 38), \
                  '16':(139, 26, 26), \
                  '17':(205, 51, 51), \
                  '18':(205, 112, 84), \
                  '19':(238, 149, 114), \
                  '20':(238, 154, 0), \
                  '21':(205, 133, 0), \
                  '22':(139, 90, 0), \
                  '23':(238, 118, 0), \
                  '24':(238, 106, 80), \
                  '25':(255, 0, 0), \
                  '26':(255, 20, 147), \
                  '27':(205, 16, 118), \
                  '28':(139, 10, 80), \
                  '29':(205, 96, 144)
                  }
        self.segment_color = (135, 206, 250)
        self.reading_order_color = (139, 35, 35)
        self.lingking_color = (50, 205, 50)
        self.word_color = (0, 0, 238)
        self.font_aspect_ratio = 0.6
        self.entity_types = {}
        
    def set_type_colors(self, type_colors):
        # 设置不同类型所对应的颜色
        self.type_colors = type_colors

    def set_segment_color(self, color):
        # 设置segment对应的颜色
        self.segment_color = color

    def set_readin_order_color(self, color):
        # 设置阅读顺序对应的颜色
        self.reading_ordercolor = color

    def set_linking_color(self, color):
        # 设置linking对应的颜色
        self.linking_color = color

    def set_word_color(self, color):
        # 设置word对应的颜色
        self.word_color = color

    def set_entity_types(self, entity_types):
        # 设置实体类型
        self.entity_types = entity_types

    def __format_box(self, raw_box):
        # 框转换为后续处理需要的类型(四点元组)
        box = []
        if isinstance(raw_box[0], int):
            # use two points, transfer it into four points
            box.append((raw_box[0], raw_box[1]))
            box.append((raw_box[2], raw_box[1]))
            box.append((raw_box[2], raw_box[3]))
            box.append((raw_box[0], raw_box[3]))
        else:
            # use four points, transfer them into tuple
            box.append(tuple(raw_box[0]))
            box.append(tuple(raw_box[1]))
            box.append(tuple(raw_box[2]))
            box.append(tuple(raw_box[3]))
        return box

    def __get_entity_name(self, entity, word_txts, get_wordpos_by_id, use_entity_text=False, use_entity_type=False):
        entity_elements = entity['word_idx']
        if use_entity_text:
            if use_entity_type: entity_name = entity['label']+'-'
            else: entity_name = ''
            for element in entity_elements:
                if element in get_wordpos_by_id:
                    element_pos = get_wordpos_by_id[element]
                    entity_name += word_txts[element_pos]
        else:
            entity_name = entity['label']
        return entity_name

    def __get_entity_box(self, entity, w, h, word_boxes, get_wordpos_by_id):
        entity_elements = entity['word_idx']
        entity_box = [w, h, 0, 0]
        for element in entity_elements:
            if element in get_wordpos_by_id:
                element_pos = get_wordpos_by_id[element]
                word_box = word_boxes[element_pos]
                # get entity box
                entity_box[2] = max(entity_box[2], word_box[0][0], word_box[1][0],word_box[2][0], word_box[3][0])
                entity_box[0] = min(entity_box[0], word_box[0][0], word_box[1][0],word_box[2][0], word_box[3][0])
                entity_box[1] = min(entity_box[1], word_box[0][1], word_box[1][1],word_box[2][1], word_box[3][1])
                entity_box[3] = max(entity_box[3], word_box[0][1], word_box[1][1],word_box[2][1], word_box[3][1])
        return entity_box

    def __get_json_info(self, 
                      json, 
                      img_size,
                      use_entity_type=False,
                      use_entity_text=False
                      ):
        # 获得json文件中的信息
        segment_boxes = []
        segment_txts = []
        segment_orders = []
        word_boxes = []
        word_txts = []
        get_word_txt_by_box = {}
        wordnum = 10000
        word_entity_paints = [None] * wordnum
        get_wordpos_by_id = {}
        wordpos = 0

        if 'label_segment_order' in json:
            segment_orders_map = json['label_segment_order']
            segment_orders = []

        for doc in json['document']:
            raw_segmemt_box = doc['box']
            segment_box = self.__format_box(raw_segmemt_box)
            segment_boxes.append(segment_box)
            segment_txt = doc['text']
            segment_txts.append(segment_txt)
            if 'label_segment_order' in json:
                segment_orders.append(segment_orders_map.index(doc['id']))
            words = doc['words']
            for word in words:
                if 'box' in word:
                    raw_word_box = word['box']
                    word_box = self.__format_box(raw_word_box)
                    word_boxes.append(word_box)
                    word_txt = word['text']
                    word_txts.append(word_txt)
                    word_id = word['id'] if 'id' in word else wordpos
                    get_wordpos_by_id[word_id] = wordpos
                    if word_box == segment_box:
                        # the word has same box with the segment, it shouldn't be paint
                        word_entity_paints[word_id] = False
                    else:
                        word_entity_paints[word_id] = True
                    wordpos += 1
                    if tuple(word_box) in get_word_txt_by_box:
                        # append the text to the contents now
                        get_word_txt_by_box[tuple(word_box)] += word['text']
                    else:
                        get_word_txt_by_box[tuple(word_box)] = word['text']
        word_entity_ids = [None] * wordpos
        word_entity_types = [None] * wordpos
        entity_names = []
        entity_boxes = []
        entity_color_types = []
        entity_ids = []
        get_entitypos_by_id = {}
        entity_pos = 0
        if 'label_entities' in json:
            for entity in json['label_entities']:
                entity_color_type = self.entity_types[entity['label']]
                entity_elements = entity['word_idx']
                entity_id = entity['entity_id']
                entity_name = self.__get_entity_name(entity, word_txts, get_wordpos_by_id, use_entity_text=use_entity_text, use_entity_type=use_entity_type)
                entity_box = self.__get_entity_box(entity, img_size[1], img_size[0], word_boxes, get_wordpos_by_id)
                for element in entity_elements:
                    if element in get_wordpos_by_id:
                        element_pos = get_wordpos_by_id[element]
                        word_entity_ids[element_pos] = entity_pos
                        word_entity_types[element_pos] = entity_color_type
                entity_names.append(entity_name)
                entity_boxes.append(entity_box)
                entity_ids.append(entity_id)
                get_entitypos_by_id[entity_id] = entity_pos
                entity_color_types.append(entity_color_type)
                entity_pos += 1
        else:
            word_entity_paints = [None] * wordpos

        label_linkings = []
        if 'label_linkings' in json:
            # formant label_linkings
            for label_linking in json['label_linkings']:
                entity1_id = label_linking[0]
                entity2_id = label_linking[1]
                if entity1_id in get_entitypos_by_id and entity2_id in get_entitypos_by_id:
                    entity1_pos = get_entitypos_by_id[entity1_id]
                    entity2_pos = get_entitypos_by_id[entity2_id]
                    label_linkings.append((entity1_pos, entity2_pos))
        return segment_boxes, word_boxes, segment_txts, word_txts, segment_orders, word_entity_ids, word_entity_types, word_entity_paints, entity_names, entity_boxes, get_word_txt_by_box, label_linkings, entity_color_types

    def __set_tag_size(self, w, h):
        base = min(w, h)
        return int(base / 50), int(base / 50)
    
    def __draw_txt_in_segment(self,
            img_size, 
            box, 
            txt, 
            font_path="./fonts/simfang.ttf"):
        box_height = int(
            math.sqrt((box[0][0] - box[3][0])**2 + (box[0][1] - box[3][1])**2))
        box_width = int(
            math.sqrt((box[0][0] - box[1][0])**2 + (box[0][1] - box[1][1])**2))

        img_text = Image.new('RGB', (box_width, box_height), (255, 255, 255))
        draw_text = ImageDraw.Draw(img_text)
        if txt:
            font = self.__create_font(txt, (box_width, box_height), font_path)
            draw_text.text([0, 0], txt, fill=(0, 0, 0), font=font)
        img_box = img_text

        pts1 = np.float32(
            [[0, 0], [box_width, 0], [box_width, box_height], [0, box_height]])
        pts2 = np.array(box, dtype=np.float32)
        M = cv2.getPerspectiveTransform(pts1, pts2)

        img_box = np.array(img_box, dtype=np.uint8)
        img_right_text = cv2.warpPerspective(
            img_box,
            M,
            img_size,
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255))
        return img_right_text
    
    def __draw_order(self,
            img_size, 
            box, 
            order, 
            color,
            reading_order_size,
            font_path="./fonts/微软雅黑.ttf"):
        box_width = reading_order_size
        box_height = reading_order_size
        img_order = Image.new('RGB', (box_width, box_height), (255, 255, 255))
        draw_order = ImageDraw.Draw(img_order)
        font = self.__create_font(str(order), (box_width, box_height), font_path)
        draw_order.text([0, 0], str(order), fill=color, font=font)
        img_box = img_order

        pts1 = np.float32(
            [[0, 0], [box_width, 0], [box_width, box_height], [0, box_height]])
        pts2 = np.array((box), dtype=np.float32)
        M = cv2.getPerspectiveTransform(pts1, pts2)

        img_box = np.array(img_box, dtype=np.uint8)
        img_right_order= cv2.warpPerspective(
            img_box,
            M,
            img_size,
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255))
        return img_right_order
    
    def __draw_entity_name(self,
                img_size, 
                box, 
                ename, 
                color,
                char_cnt,
                entity_tag_height,
                font_path="./fonts/微软雅黑.ttf"):
        box_width = int(char_cnt * self.font_aspect_ratio * entity_tag_height)
        box_height = entity_tag_height
        img_entity = Image.new('RGB', (box_width, box_height), (255, 255, 255))
        draw_entity = ImageDraw.Draw(img_entity)
        if ename:
            font = self.__create_font(ename, (box_width, box_height), font_path)
            draw_entity.text([0, 0], ename, fill=color, font=font)
        img_box = img_entity

        pts1 = np.float32(
            [[0, 0], [box_width, 0], [box_width, box_height], [0, box_height]])
        pts2 = np.array((box), dtype=np.float32)
        M = cv2.getPerspectiveTransform(pts1, pts2)

        img_box = np.array(img_box, dtype=np.uint8)
        img_right_entity= cv2.warpPerspective(
            img_box,
            M,
            img_size,
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255))
        return img_right_entity
    
    def __create_font(self, txt, sz, font_path="./fonts/simfang.ttf"):
        font_size = int(sz[1] * 0.99)
        font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
        length = font.getsize(txt)[0]
        if length > sz[0]:
            font_size = int(font_size * sz[0] / length)
            font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
        return font
    
    def __draw_txt_in_word(self, 
                         img_size, 
                      box, 
                      txt, 
                      font_path="./fonts/simfang.ttf"):
        box_height = int(
            math.sqrt((box[0][0] - box[3][0])**2 + (box[0][1] - box[3][1])**2))
        box_width = int(
            math.sqrt((box[0][0] - box[1][0])**2 + (box[0][1] - box[1][1])**2))
        
        img_text = Image.new('RGB', (box_width, box_height), (255, 255, 255))
        draw_text = ImageDraw.Draw(img_text)
        if txt:
            font = self.__create_font(txt, (box_width, box_height), font_path)
            draw_text.text([0, 0], txt, fill=(0, 0, 0), font=font)
        img_box = img_text

        pts1 = np.float32(
            [[0, 0], [box_width, 0], [box_width, box_height], [0, box_height]])
        pts2 = np.array(box, dtype=np.float32)
        M = cv2.getPerspectiveTransform(pts1, pts2)

        img_box = np.array(img_box, dtype=np.uint8)
        img_right_text = cv2.warpPerspective(
            img_box,
            M,
            img_size,
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255))
        return img_right_text

    def __draw_annotation(self,
            img_size,
            segment_boxes,
            word_boxes,
            use_segment_text,
            use_word=False,
            use_entity_type=False,
            use_entity_text=False,
            use_linking=False,
            use_order=False,
            segment_txts=None,
            word_txts=None,
            segment_orders=None,
            word_entity_ids=None,
            word_entity_types=None,
            word_entity_paints=None,
            entity_names=None,
            entity_boxes=None,
            get_word_txt_by_box=None,
            label_linkings=None,
            entity_color_types=None,
            font_path="./fonts/simfang.ttf"):
        # 绘制右图

        # 创建画布
        h, w = img_size
        img = np.ones((h, w, 3), dtype=np.uint8) * 255
        
        entity_tag_height, reading_order_size = self.__set_tag_size(w, h)

        use_entity = use_entity_type | use_entity_text

        if use_word == False and (segment_txts is None or len(segment_txts) != len(segment_boxes)):
            print("illegal segment text")
        if use_order == True and (segment_orders is None or len(segment_orders) != len(segment_boxes)):
            print("illegal segment order")
        if use_word == True and (word_txts is None or len(word_txts) != len(word_boxes)):
            print("illegal word text")
        if use_entity == True and (word_entity_ids is None or len(word_entity_ids) != len(word_boxes)):
            print("illegal entity id")
            use_entity = False
        if use_entity == True and (word_entity_types is None or len(word_entity_types) != len(word_boxes)):
            print("illegal entity types")
            use_entity = False
        
        # draw segment boxes
        if use_order == False:
            segment_orders = [None] * len(segment_boxes)
        for idx, (box, txt, order) in enumerate(zip(segment_boxes,
                                                    segment_txts, 
                                                    segment_orders)):
            color = self.segment_color
            # draw_left1.polygon(box, fill=color)
            # draw_left1.rectangle(, fill=(0, 0, 0))
            img_segment_text = np.ones((h, w, 3), dtype=np.uint8) * 255 
            cv2.rectangle(img_segment_text, box[0], box[2], self.segment_color, 1)
            img = cv2.bitwise_and(img, img_segment_text)
            if use_word == False:
                img_right_text = self.__draw_txt_in_segment((w, h), box, txt, font_path)
                pts = np.array(box, np.int32).reshape((-1, 1, 2))
                cv2.polylines(img_right_text, [pts], True, color, 1)
                img = cv2.bitwise_and(img, img_right_text)
            # draw reading order
            if use_order:
                order_box = ([[box[0][0]-reading_order_size, box[0][1]], [box[0][0], box[0][1]], [box[0][0], box[0][1]+reading_order_size], [box[0][0]-reading_order_size, box[0][1]+reading_order_size]])
                img_right_order = self.__draw_order(img_size=( w, h), box=order_box, order=order, color=self.reading_order_color, reading_order_size=reading_order_size)
                pts = np.array(order_box, np.int32).reshape((-1, 1, 2))
                cv2.polylines(img_right_order, [pts], True, self.reading_order_color, 1)
                img = cv2.bitwise_and(img, img_right_order)

        # draw word boxes (abandoned now)
        # for idx, (box, txt, eid, type, paint) in enumerate(zip(word_boxes, 
        #                                                        word_txts, 
        #                                                        word_entity_ids, 
        #                                                        word_entity_types, 
        #                                                        word_entity_paints)):
        #     if paint:
        #         color = type_color_dic[str(type)]
        #         if use_entity_id:
        #             if use_entity:
        #                 # draw word_id at upper left
        #                 entity_id_box = ([[box[0][0]-entity_tag_height, box[0][1]], [box[0][0], box[0][1]], [box[0][0], box[0][1]+entity_tag_height], [box[0][0]-entity_tag_height, box[0][1]+entity_tag_height]])
        #                 img_right_entity_id = draw_entity_id((w, h), entity_id_box, eid, color, font_path, entity_tag_height=entity_tag_height)
        #                 pts = np.array(entity_id_box, np.int32).reshape((-1, 1, 2))
        #                 cv2.polylines(img_right_entity_id, [pts], True, (255, 255, 255), 1)
        #                 img = cv2.bitwise_and(img, img_right_entity_id)
        # draw words
        if use_word == True:
            if get_word_txt_by_box != None:
                for box, content in get_word_txt_by_box.items():
                    img_right_text = self.__draw_txt_in_word((w, h), box, content, font_path)
                    pts = np.array(box, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img_right_text, [pts], True, (255, 255, 255), 1)
                    cv2.rectangle(img_right_text, box[0], box[2], self.word_color, 1)
                    img = cv2.bitwise_and(img, img_right_text)

        # draw entity
        # 绘制实体内容
        if entity_boxes != None:
            for idx, (box, name, type) in enumerate(zip(entity_boxes, 
                                                    entity_names,
                                                    entity_color_types)):
                color = self.type_colors[str(type)]
                char_cnt = len(name)
                if use_entity:
                    # draw entity at upper left
                    entity_box = ([[box[0], box[1]-entity_tag_height], \
                                [box[0]+int(char_cnt * self.font_aspect_ratio * entity_tag_height), box[1]-entity_tag_height], \
                                [box[0]+int(char_cnt * self.font_aspect_ratio * entity_tag_height), box[1]], \
                                [box[0], box[1]]])
                    img_right_entity = self.__draw_entity_name((w, h), box=entity_box, ename=name, color=color, char_cnt=char_cnt, entity_tag_height=entity_tag_height)
                    pts = np.array(entity_box, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img_right_entity, [pts], True, color, 1)
                    img = cv2.bitwise_and(img, img_right_entity)

        # draw label linkings
        if use_linking == True:
            if label_linkings != None and entity_boxes != None:
                for label_lingking in label_linkings:
                    label1 = label_lingking[0]
                    label2 = label_lingking[1]
                    label1_box = entity_boxes[label1]
                    label2_box = entity_boxes[label2]
                    label1_point = ((label1_box[0]+label1_box[2])//2, (label1_box[1]+label1_box[3])//2)
                    label2_point = ((label2_box[0]+label2_box[2])//2, (label2_box[1]+label2_box[3])//2)
                    img_linking = np.array(Image.new('RGB', (w, h), (255, 255, 255)), dtype=np.uint8)
                    cv2.line(img_linking, label1_point, label2_point, self.lingking_color, 1, 4)
                    img = cv2.bitwise_and(img, img_linking)
            else: 
                print("illegal linking data")

        return np.array(img)
    
    def __get_border(self, json):
        # 推导边框
        max_w = 0
        max_h = 0
        min_w = float("inf")
        min_h = float("inf")
        for seg in json['document']:
            box = seg['box']
            box = self.__format_box(box)
            max_w = max(box[0][0], box[1][0], box[2][0], box[3][0], max_w)
            max_h = max(box[0][1], box[1][1], box[2][1], box[3][1], max_h)
            min_w = min(box[0][0], box[1][0], box[2][0], box[3][0], min_w)
            min_h = min(box[0][0], box[1][0], box[2][0], box[3][0], min_h)
            for word in seg['words']:
                box = word['box']
                box = self.__format_box(box)
                max_w = max(box[0][0], box[1][0], box[2][0], box[3][0], max_w)
                max_h = max(box[0][1], box[1][1], box[2][1], box[3][1], max_h)
        return (max_h+min_h, max_w+min_w)

    def visualize(self,
            json, 
            save_path,
            use_image=False,
            image_path=None,
            use_word=False,
            use_entity_type=False,
            use_entity_text=False,
            use_linking=False,
            use_order=False
            ):
        # 绘制json信息
        # json是待解析的标注信息
        # save_path是可视化后图片保存位置
        # use_image是绘制左图的开关. 其为真, 则绘制左图右文, 并且需要提供image_path. 为假则只绘制文字. 
        # image_path是图像的地址
        # use_word是文+框显示级别的开关. 其为真, 则显示word级别. 为假则显示segment级别
        # use_entity_type是实体类型显示的开关
        # use_entity_text是实体内容文字显示的开关
        # use_linking是实体链接显示的开关
        # use_order是阅读顺序显示的开关

        # 判断是否使用图片及其合法性
        if use_image == True:
            # try:
            #     image = Image.open(image_path)
            # except Exception as e:
            #     print(str(e))
            #     raise e
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            img_size = (json['img']['height'], json['img']['width'])
        elif 'img' in json:
            img_size = (json['img']['height'], json['img']['width'])
        else:
            img_size = self.__get_border(json)
        
        segment_boxes, word_boxes, segment_txts, word_txts, segment_orders, word_entity_ids, word_entity_types, word_entity_paints, entity_names, entity_boxes, get_word_txt_by_box, label_linkings, entity_color_types = self.__get_json_info(json, img_size, use_entity_text=use_entity_text, use_entity_type=use_entity_type)

        # 画右图
        img_right = self.__draw_annotation(
            img_size=img_size,
            segment_boxes=segment_boxes,
            word_boxes=word_boxes,
            use_segment_text=use_entity_text,
            use_word=use_word,
            use_entity_type=use_entity_type,
            use_entity_text=use_entity_text,
            use_order=use_order,
            use_linking=use_linking,
            segment_txts=segment_txts,
            word_txts=word_txts,
            segment_orders=segment_orders,
            word_entity_ids=word_entity_ids,
            word_entity_types=word_entity_types,
            word_entity_paints=word_entity_paints,
            entity_names=entity_names,
            entity_boxes=entity_boxes,
            get_word_txt_by_box=get_word_txt_by_box,
            label_linkings=label_linkings,
            entity_color_types=entity_color_types,
            font_path="./fonts/simfang.ttf"
            )
        
        # 画左图
        if use_image:
            img_left = image.copy()
            draw_left1 = ImageDraw.Draw(img_left)
            for box in segment_boxes:
                color = self.segment_color
                draw_left1.polygon(box, fill=color)
            # img_left = Image.blend(image, img_left, 0.5)
            for box in word_boxes:
                color = self.word_color
                draw_left1.polygon(box, fill=color)
            img_left = Image.blend(image, img_left, 0.5)

        # 拼左图
        if use_image:
            img_show = Image.new('RGB', (img_size[1] * 2, img_size[0]), (255, 255, 255))
            img_show.paste(img_left, (0, 0, img_size[1], img_size[0]))
            img_show.paste(Image.fromarray(img_right), (img_size[1], 0, img_size[1] * 2, img_size[0]))
        else:
            img_show = Image.new('RGB', (img_size[1], img_size[0]), (255, 255, 255))
            img_show.paste(Image.fromarray(img_right), (0, 0, img_size[1], img_size[0]))

        img_show.save(save_path, "PNG")