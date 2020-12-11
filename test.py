from ocr import ocr_recognition

img_path = './ocr/test_imgs/030802.jpg'
ocr_detection_model, ocr_recognition_modelA, ocr_recognition_modelB, ocr_label_dict = ocr_recognition.init_ocr_model(0)
ocr_recognition.ocr_recognition(img_path, ocr_detection_model, ocr_recognition_modelA, ocr_label_dict, 299)