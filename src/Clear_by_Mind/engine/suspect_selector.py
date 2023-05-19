#!/usr/bin/env python

import random
import math
import os
import shutil
import subprocess

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# This module more or less does this:
#        row_no = math.floor(random.random() * 4)
#        col_no = math.floor(random.random() * 5)
#        suspect_no = row_no * 10 + col_no
# ...but with some extra rules to avoid showing the same category of suspects directly after eachother,
# ...and to even out the histogram for all classes
# ...and trying to lower the longest distance between showing suspects from the same class, since user would be bored if "his" suspects doesn't show up.

# This is a dict of all categories and the suspect_no that belongs to this category:
suspect_categories = {}
suspect_categories['hat'] = [0,1,2,3]
suspect_categories['tie'] = [10,11,12,13]
suspect_categories['briefcase'] = [20,21,22,23]
suspect_categories['skirt'] = [30,31,32,33]
suspect_categories['yellow'] = [0,10,20,30]
suspect_categories['blue'] = [1,11,21,31]
suspect_categories['green'] = [2,12,22,32]
suspect_categories['red'] = [3,13,23,33]
suspect_categories['child'] = [4,14,24,34]

suspect_category_colors = {}
suspect_category_colors['hat'] = 'grey'
suspect_category_colors['tie'] = 'grey'
suspect_category_colors['briefcase'] = 'grey'
suspect_category_colors['skirt'] = 'grey'
suspect_category_colors['yellow'] = 'yellow'
suspect_category_colors['blue'] = 'blue'
suspect_category_colors['green'] = 'green'
suspect_category_colors['red'] = 'red'
suspect_category_colors['child'] = 'magenta'

category_nos = {}
category_nos['hat'] = 0
category_nos['tie'] = 1
category_nos['briefcase'] = 2
category_nos['skirt'] = 3
category_nos['yellow'] = 4
category_nos['blue'] = 5
category_nos['green'] = 6
category_nos['red'] = 7
category_nos['child'] = 8

category_ids = {}
category_ids[0] = 'hat'
category_ids[1] = 'tie'
category_ids[2] = 'briefcase'
category_ids[3] = 'skirt'
category_ids[4] = 'yellow'
category_ids[5] = 'blue'
category_ids[6] = 'green'
category_ids[7] = 'red'
category_ids[8] = 'child'

epoch_no = 0
least_recently_used_seed = {}
least_recently_used = {}
chosen_suspects = []
chosen_suspect_categories = []
chosen_rows = []
chosen_columns = []
suspect_histogram = {}
row_histogram = {}
column_histogram = {}
verbosity_level = 0

def init(with_verbosity=0):
  verbosity_level = with_verbosity
  epoch_no = 0
  # A dictionary with one entry per suspect, with a number telling at which epoch
  # this suspect was last shown.

  # Start by seeding this list by randomizing numbers between ]-20.0 and 0.0]:
  for row_no in range(4):
    for col_no in range(5):
      suspect_no = row_no * 10 + col_no
      least_recently_used_seed[suspect_no] = -20.0 * random.random()

  if verbosity_level > 0:
    # Debug printing of the results:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("least_recently_used_seed[%02d]=%5f" % (suspect_no, least_recently_used_seed[suspect_no]))

  # Sort the randomization seeds to get an initial randomized sequence with all the suspects.
  sort_order = sorted(least_recently_used_seed.items(), key=lambda x: x[1], reverse=True)
  # The epoch number to start from when inserting this initial randomized sequence:
  current_epoch_no = -20
  for suspect_no in sort_order:
    #print(suspect_no[0], suspect_no[1])
    least_recently_used[suspect_no[0]] = current_epoch_no
    current_epoch_no += 1

  # Now we have a randomized history of virtual epochs in the least_recently_used_dictionary
  if verbosity_level > 0:
    # Debug printing of the results:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("least_recently_used[%02d]=%d" % (suspect_no, least_recently_used[suspect_no]))
    print("---")

  # Initialize histograms:
  for row_no in range(4):
    for col_no in range(5):
      suspect_no = row_no * 10 + col_no
      suspect_histogram[suspect_no] = 0
  for row_no in range(4):
    row_histogram[row_no] = 0
  for col_no in range(5):
    column_histogram[col_no] = 0


def get_next_suspect():
  # Put all 20 suspects into the bag, with an initial score from 2005 to 2100 depending on least_recently_used:
  next_suspect_score = {}
  current_score = 2005
  # Sort the randomization seeds to get an initial randomized sequence with all the suspects.
  suspect_order = sorted(least_recently_used.items(), key=lambda x: x[1], reverse=True)
  for suspect_no in suspect_order:
    next_suspect_score[suspect_no[0]] = current_score
    current_score += 5
  if verbosity_level > 0:
    # Debug printing of the results:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("next_suspect_score[%02d]=%d" % (suspect_no, next_suspect_score[suspect_no]))
    print("Reducing score for the row chosen in the last epoch:")

  previous_row = -1
  try:
    previous_row = chosen_rows[-1]
  except:
    pass
  if verbosity_level > 0:
    print("Row #%d was used in the last epoch" % previous_row)
  if previous_row >= 0:
    # Don't reduce the score for the non-suspects here, so range(4) instead of range(5):
    for col_no in range(4):
      suspect_no = previous_row * 10 + col_no
      next_suspect_score[suspect_no] -= 152

  if verbosity_level > 0:
    print("Reducing score for the row chosen two epochs ago:")
  previous2_row = -1
  try:
    previous2_row = chosen_rows[-2]
  except:
    pass
  if verbosity_level > 0:
    print("Row #%d was used two epochs ago" % previous2_row)
  if previous2_row >= 0:
    # Don't reduce the score for the non-suspects here, so range(4) instead of range(5):
    for col_no in range(4):
      suspect_no = previous2_row * 10 + col_no
      next_suspect_score[suspect_no] -= 24

  if verbosity_level > 0:
    print("Reducing score for the column chosen in the last epoch:")
  previous_column = -1
  try:
    previous_column = chosen_columns[-1]
  except:
    pass
  if verbosity_level > 0:
    print("Column #%d was used in the last epoch" % previous_column)
  if previous_column >= 0:
    for row_no in range(4):
      suspect_no = row_no * 10 + previous_column
      next_suspect_score[suspect_no] -= 222

  if verbosity_level > 0:
    print("Reducing score for the column chosen two epochs ago:")
  previous2_column = -1
  try:
    previous2_column = chosen_columns[-2]
  except:
    pass
  if verbosity_level > 0:
    print("Column #%d was used two epochs ago" % previous2_column)
  if previous2_column >= 0:
    for row_no in range(4):
      suspect_no = row_no * 10 + previous2_column
      next_suspect_score[suspect_no] -= 54

  if verbosity_level > 0:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("next_suspect_score[%02d]=%d" % (suspect_no, next_suspect_score[suspect_no]))
    print("---")
    print("Adjusting scores depending on histogram on how many times a suspect has been shown previously:")

  for row_no in range(4):
    for col_no in range(5):
      suspect_no = row_no * 10 + col_no
      next_suspect_score[suspect_no] -= 120 * suspect_histogram[suspect_no]

  if verbosity_level > 0:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("next_suspect_score[%02d]=%d" % (suspect_no, next_suspect_score[suspect_no]))
    print("---")

  # Here, choose between showing suspects or non-suspects.
  # But only show non-suspects if they haven't been shown recently.
  if previous_column == 4:
    probability_for_showing_a_non_suspect = 0.0
  elif previous2_column == 4:
    probability_for_showing_a_non_suspect = 0.06
  else:
    probability_for_showing_a_non_suspect = 0.15

  doing_a_suspect = True
  if random.random() < probability_for_showing_a_non_suspect:
    if verbosity_level > 0:
      print("Let's show a non suspect, so lower score for all suspects:")
    for row_no in range(4):
      for col_no in range(4):
        suspect_no = row_no * 10 + col_no
        next_suspect_score[suspect_no] -= 400
    doing_a_suspect = False
  else:
    if verbosity_level > 0:
      print("Let's show a suspect, so lower score for all non-suspects:")
    for row_no in range(4):
      suspect_no = row_no * 10 + 4
      next_suspect_score[suspect_no] -= 400

  if verbosity_level > 0:
    for row_no in range(4):
      for col_no in range(5):
        suspect_no = row_no * 10 + col_no
        print("next_suspect_score[%02d]=%d" % (suspect_no, next_suspect_score[suspect_no]))
    print("---")

  # Now let's select one of the top three candidates:
  if verbosity_level > 0:
    print("Top #3 candidates:")
  suspect_order = sorted(next_suspect_score.items(), key=lambda x: x[1], reverse=True)
  top_candidates = []
  if verbosity_level > 0:
    print(suspect_order)
  for top_no in range(3):
    suspect_no = suspect_order[top_no][0]
    suspect_score = suspect_order[top_no][1]
    if verbosity_level > 0:
      print("next_suspect_score[%02d]=%d" % (suspect_no, suspect_score))
    top_candidates.append(suspect_no)

  if verbosity_level > 0:
    print(top_candidates)

  if doing_a_suspect == True:
    # With equal probability, choose one of the top three candidates:
    chosen_index = math.floor(random.random() * 3.0)
  else:
    # When showing non suspects, always show the topmost one. This evens out the histogram distance between non-suspects,
    # since there are only four non-suspects to choose from.
    chosen_index = 0
  chosen_suspect = top_candidates[chosen_index]
  chosen_column = chosen_suspect % 10
  column_histogram[chosen_column] += 1
  if chosen_column <= 3:
    chosen_row = chosen_suspect // 10
    chosen_rows.append(chosen_row)
    row_histogram[chosen_row] += 1
  else:
    chosen_row = -1
    chosen_rows.append(chosen_row)

  chosen_suspects.append(chosen_suspect)
  chosen_columns.append(chosen_column)
  suspect_histogram[chosen_suspect] += 1

  if verbosity_level > 0:
    print("chosen_suspect=%d" % chosen_suspect)
    print("chosen_row=%d" % chosen_row)
    print("chosen_column=%d" % chosen_column)
    print("chosen_suspects=")
    print(chosen_suspects)

  return chosen_suspect


if __name__ == "__main__":
  print("### Prototype suspect selector self tests")

  # Use debug prints when running self tests:
  init(1)
  for current_epoch_no in range(1000):
    print("### Starting selection for epoch no #%d:" % current_epoch_no)
    get_next_suspect()
  print("suspect_histogram=")
  print(suspect_histogram)
  print("row_histogram=")
  print(row_histogram)
  print("column_histogram=")
  print(column_histogram)


  # Plot metadata about the sequence we've gotten:
  suspect_category_distances = {}
  for suspect_category in suspect_categories:
    print("Suspect category = %s" % suspect_category)
    suspect_category_distances[suspect_category] = []
    last_found_in_epoch_no = -1
    for epoch_no in range(len(chosen_suspects)):
      for suspect_no in suspect_categories[suspect_category]:
        if chosen_suspects[epoch_no] == suspect_no:
          if last_found_in_epoch_no != -1:
            distance = epoch_no - last_found_in_epoch_no
            suspect_category_distances[suspect_category].append(distance)
          last_found_in_epoch_no = epoch_no

  f, ax = plt.subplots(3, 3, sharey=True, sharex=True, tight_layout=True)
  f.suptitle(
    "Histogram of suspect category spacing",
    y=0.025,
    x=0.01,
    ha="left",
  )
  # f.subplots_adjust(top=0.5)
  col_no = 0
  row_no = 0
  for suspect_category in suspect_categories:
    print("Suspect category = %s" % suspect_category)
    bins=range(np.asarray(suspect_category_distances[suspect_category]).max())
    ax[row_no][col_no].hist(suspect_category_distances[suspect_category], color=suspect_category_colors[suspect_category], ec='black', bins=bins, lw=0.25)
    ax[row_no][col_no].set_xlabel("distance")
    ax[row_no][col_no].set_ylabel("nof_occurences")
    ax[row_no][col_no].set_title("%s" % suspect_category)
    ax[row_no][col_no].set_xlim(left=0)
#      max_amplitude = 5
#      ax[plot_no].set_ylim(0, max_amplitude)
#      ax[plot_no].set_xlim(0, nof_seconds)
    col_no += 1
    if col_no == 3:
      col_no = 0
      row_no += 1
  plt.tight_layout()
  plt.savefig("suspect_category_spacing_histogram.png", dpi=300)
  plt.close(f)


  # Calculate a separate histogram for each and every suspect for the distance between the occasions when it's shown:
  suspect_distances = {}
  for row_no in range(4):
    for col_no in range(5):
      suspect_no = row_no * 10 + col_no
      suspect_distances[suspect_no] = []
      last_found_in_epoch_no = -1
      for epoch_no in range(len(chosen_suspects)):
        if chosen_suspects[epoch_no] == suspect_no:
          if last_found_in_epoch_no != -1:
            distance = epoch_no - last_found_in_epoch_no
            suspect_distances[suspect_no].append(distance)
          last_found_in_epoch_no = epoch_no

  # https://matplotlib.org/tutorials/introductory/customizing.html
  plt.rcParams.update({"font.size": 6})
  plt.rcParams.update({"font.family": "Arial"})
  # plt.rcParams.update({'font.weight': 'bold'}) # = 700
  plt.rcParams.update({"font.weight": "900"})

  f, ax = plt.subplots(4, 5, sharey=True, sharex=True, tight_layout=True)
  f.suptitle(
    "Histogram of suspect spacing",
    y=0.025,
    x=0.01,
    ha="left",
  )
  # f.subplots_adjust(top=0.5)
  suspect_column_colors = ['yellow','blue','green','red','magenta']
  plot_no = 0
  for row_no in range(4):
    for col_no in range(5):
      suspect_no = row_no * 10 + col_no

      # We can set the number of bins with the *bins* keyword argument.
      bins=range(np.asarray(suspect_distances[suspect_no]).max())
      ax[row_no][col_no].hist(suspect_distances[suspect_no], color=suspect_column_colors[col_no], ec='black', bins=bins, lw=0.25)
      ax[row_no][col_no].set_xlabel("distance")
      ax[row_no][col_no].set_ylabel("nof_occurences")
      ax[row_no][col_no].set_title("susp#%d%d" % (row_no, col_no))
#      max_amplitude = 5
#      ax[plot_no].set_ylim(0, max_amplitude)
      ax[row_no][col_no].set_xlim(left=0)
      plot_no += 1
  plt.tight_layout()
  plt.savefig("suspect_spacing_histogram.png", dpi=300)
  plt.close(f)


  # Make a video of how the histogram of classes grow:
  make_video = True
  if make_video:
    # https://matplotlib.org/tutorials/introductory/customizing.html
    plt.rcParams.update({"font.size": 10})
    plt.rcParams.update({"font.family": "Arial"})
    plt.rcParams.update({"font.weight": "900"})
    fig_folder = "histogram_video"
    if not os.path.exists(fig_folder):
      os.makedirs(fig_folder)
    for frame_no in range(len(chosen_suspects)):
      # assuming 200ms for showing each suspect:
      the_time = 0.2 * frame_no
      print("Plotting histogram for epoch no=%d" % frame_no)
      f, ax = plt.subplots(1, 1, tight_layout=True)
      f.suptitle(
        "Epoch_no=%03d, Session time = %.2f seconds" % (frame_no, the_time),
        y=0.025,
        x=0.01,
        ha="left",
      )

      # Now translate suspect_nos into categories.
      suspect_nos_in_the_selected_epochs = chosen_suspects[0:frame_no+1]
      chosen_suspect_category_nos = []
      # NOTE: A suspect belongs to more than one category!
      # Calculate the category that was chosen:
      for this_suspect_no in suspect_nos_in_the_selected_epochs:
        for category_id in suspect_categories:
          for suspect_no in suspect_categories[category_id]:
            if this_suspect_no == suspect_no:
              category_no = category_nos[category_id]
              chosen_suspect_category_nos.append(category_no)
      plot_data = chosen_suspect_category_nos

      # We can set the number of bins with the *bins* keyword argument.
      bins=range(len(category_nos)+1)
      N, the_bins, patches = ax.hist(plot_data, color='grey', edgecolor='black', bins=bins, lw=0.25)
      ax.set_xlabel("category_no")
      ax.set_ylabel("nof_occurences")
      ax.set_title("Histogram of shown suspect categories")
#      max_amplitude = 5
#      ax[plot_no].set_ylim(0, max_amplitude)
      ax.set_xlim(left=0)
      ax.set_ylim(bottom=0)

      # Set the colors of the bars:
      for category_no in range(len(category_nos)):
        patches[category_no].set_facecolor(suspect_category_colors[category_ids[category_no]])
      # Set the labels of the bars:
      labels = ["%s" % category_id for category_id in suspect_categories]
      for rect, label in zip(patches, labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height+0.01, label, ha='center', va='bottom')

      f.savefig("%s/hist_at_epoch_no_%03d.png" % (fig_folder, frame_no), bbox_inches="tight")
      plt.close(f)

    # Make a video of these files:
    # Duplicate the last frame to make sure that it gets encoded:
    nof_extra_frames = 30
    nof_frames = len(chosen_suspects)
    for extra_frame_no in range(1, nof_extra_frames):
      shutil.copy(
        "%s/hist_at_epoch_no_%03d.png" % (fig_folder, nof_frames - 1),
        "%s/hist_at_epoch_no_%03d.png" % (fig_folder, nof_frames - 1 + extra_frame_no),
      )
    video_filename = "video_of_suspect_class_histogram.mp4"
    # ffmpeg stc_%03d.png -c:v libx264 -preset slow -crf 6 -filter:v "crop=660:482:0:0,fps=60" -pix_fmt yuv420p -y video.mp4
    # subprocess.run(["ffmpeg","-i",fig_folder+"/stc_%03d.png","-c:v","libx264","-preset","slow","-crf","6","-filter:v",'crop=660:482:0:0,fps=60',"-pix_fmt","yuv420p","-y",video_filename], capture_output=True)
    # subprocess.run(["ffmpeg","-i",fig_folder+"/stc_%03d.png","-c:v","libx264","-preset","slow","-crf","6","-filter:v",'fps=60',"-pix_fmt","yuv420p","-y",video_filename], capture_output=True)
    subprocess.run(
      [
        "ffmpeg",
        "-i",
        fig_folder + "/hist_at_epoch_no_%03d.png",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "6",
        "-filter:v",
        "pad=ceil(iw/2)*2:ceil(ih/2)*2,fps=60",
        "-pix_fmt",
        "yuv420p",
        "-y",
        video_filename,
      ],
      capture_output=True,
    )
