# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
#
# Modified by Peng Tang for DPL
# --------------------------------------------------------

"""Compute minibatch blobs for training a Fast R-CNN network."""

import numpy as np
import numpy.random as npr
import cv2
from fast_rcnn.config import cfg
from utils.blob import prep_im_for_blob, im_list_to_blob

def get_minibatch(roidb, num_classes):
    """Given a roidb, construct a minibatch sampled from it."""
    num_images = len(roidb)
    # Sample random scales to use for each image in this batch
    random_scale_inds = npr.randint(0, high=len(cfg.TRAIN.SCALES),
                                    size=num_images)

    # Get the input image blob, formatted for caffe
    im_blob, im_scales, im_shapes = _get_image_blob(roidb, random_scale_inds)

    # Now, build the region of interest and label blobs
    rois_blob = np.zeros((0, 5), dtype=np.float32)
    labels_blob = np.zeros((0, 20), dtype=np.float32)
    # bbox_targets_blob = np.zeros((0, 4 * num_classes), dtype=np.float32)
    # bbox_loss_blob = np.zeros(bbox_targets_blob.shape, dtype=np.float32)
    # all_overlaps = []
    for im_i in xrange(num_images):
        labels, im_rois = _sample_rois(roidb[im_i], num_classes)

        # Add to RoIs blob
        rois = _project_im_rois(im_rois, im_scales[im_i])
        batch_ind = im_i * np.ones((rois.shape[0], 1))
        rois_blob_this_image = np.hstack((batch_ind, rois))
        rois_blob = np.vstack((rois_blob, rois_blob_this_image))

        # Add to labels, bbox targets, and bbox loss blobs
        labels_blob = np.vstack((labels_blob, labels))
        # all_overlaps = np.hstack((all_overlaps, overlaps))

    # For debug visualizations
    # _vis_minibatch(im_blob, rois_blob, labels_blob, all_overlaps)
    blobs = {'data': im_blob,
             'rois': rois_blob,
             'labels': labels_blob,
             'shapes': im_shapes}

    return blobs

def _sample_rois(roidb, num_classes):
    """Generate a random sample of RoIs comprising foreground and background
    examples.
    """
    # label = class RoI has max overlap with
    labels = roidb['labels']
    rois = roidb['boxes']
    num_rois = len(rois)

    keep_inds = npr.choice(num_rois, size=num_rois, replace=False)
    rois = rois[keep_inds]

    return labels, rois

def _get_image_blob(roidb, scale_inds):
    """Builds an input blob from the images in the roidb at the specified
    scales.
    """
    num_images = len(roidb)
    processed_ims = []
    im_scales = []
    im_shapes = np.zeros((0, 2), dtype=np.float32)
    for i in xrange(num_images):
        im = cv2.imread(roidb[i]['image'])
        if roidb[i]['flipped']:
            im = im[:, ::-1, :]
        target_size = cfg.TRAIN.SCALES[scale_inds[i]]
        im, im_scale, im_shape = prep_im_for_blob(im, cfg.PIXEL_MEANS, target_size)
        im_scales.append(im_scale)
        processed_ims.append(im)
        im_shapes = np.vstack((im_shapes, im_shape))

    # Create a blob to hold the input images
    blob = im_list_to_blob(processed_ims)

    return blob, im_scales, im_shapes

def _project_im_rois(im_rois, im_scale_factor):
    """Project image RoIs into the rescaled training image."""
    rois = im_rois * im_scale_factor
    return rois
