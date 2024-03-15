import struct

# floatNum = -3.141592e+00
floatNum = 1.0e+00
print('Initial float: ', floatNum)

#floatNum_bytes = struct.pack('!f', floatNum) # Network
#print('Network:       ', floatNum_bytes.hex(' '))

floatNum_bytes_le = struct.pack('<f', floatNum) # little-endian
print('Little-endian: ', floatNum_bytes_le.hex(' '))

floatNum_bytes = struct.pack('>f', floatNum) # big-endian = Network ('!f')
print('Big-endian:    ', floatNum_bytes.hex(' '))


floatNum_int = int(floatNum_bytes.hex(), 16)
print('floatNum_int: ', floatNum_int, end = '') # 121366389421669 
print('  # size in bytes =', floatNum_int.__sizeof__()) # 32

word1 = (floatNum_int & 0xFFFF0000) >> 16  # Take hi  2-byte word
word2 =  floatNum_int & 0x0000FFFF         # Take low 2-byte word

print('word1 (int): ', word1)
print('word2 (int): ', word2)

print('word1 (hex): ', word1.to_bytes(2, 'big').hex(' '))
print('word2 (hex): ', word2.to_bytes(2, 'big').hex(' '))


byte1 = (word1 & 0xFF00) >> 8 # Take hi  byte of word1
byte2 =  word1 & 0xFF         # Take low byte of word1

byte3 = (word2 & 0xFF00) >> 8 # Take hi  byte of word2
byte4 =  word2 & 0xFF         # Take low byte of word2


print('Passed (by 2 words): ', struct.pack('>HH', word2, word1).hex(' '))
print('Passed (by 4 bytes): ', struct.pack('>BBBB', byte3, byte4, byte1, byte2).hex(' '))

floatNumRecieved_bytes = struct.pack('>HH', word1, word2)
print('Should be (hex, big-endian): ', floatNumRecieved_bytes.hex(' '))

floatNumNeeded = struct.unpack('>f', floatNumRecieved_bytes)[0]
print('Should be (float): ', floatNumNeeded)

#DataBuf[DataLen]     = (unsigned char) ((CurrentData & 0xFF00) >> 8);
#DataBuf[DataLen + 1] = (unsigned char) (CurrentData & 0xFF);
