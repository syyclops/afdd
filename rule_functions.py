# co2 rule
def co2_too_high(ppm: float):
  try:
    if ppm >= 1000:
      return True
    return False
  except:
    raise TypeError('Measurement must be a float. ')
  
  