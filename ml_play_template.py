"""
The template of the main script of the machine learning process
"""
import threading
import time
import importlib
import os
import os.path
import sys

class MLPlay:
    def __init__(self):
        """
        Constructor
        """
        self.ball_served = False
        self.ballpos =[]
        self.ballvel =[]

    def update(self, scene_info):
        """
        Generate the command according to the received `scene_info`.
        """
        # Make the caller to invoke `reset()` for the next round.
        if (scene_info["status"] == "GAME_OVER" or scene_info["status"] == "GAME_PASS"):
            self.ball_served = False
            self.ballpos =[]
            self.ballvel =[]
            return "RESET",''

        
        #scene_info["ball"] # 5 * 5
        #scene_info["platform"] # 40 * 5
        #scene_info["bricks"] # 25 * 10
        #scene_info["hard_bricks"] # 25 * 10
        
        ball = self.GetCenter(scene_info["ball"],(5,5))
        real = self.GetCenter(scene_info["platform"],(40,5))
        #platform = self.GetBound(scene_info["platform"],(40,5))
        form = self.GetBound((0,0),(200,400),(-2.5,-2.5))
        if len(self.ballvel)>=1: 
            speed = self.ballvel[-1]
        else:
            speed =(-7,-7)
        
        bricks =[]
        hard_bricks =[]
        for brick in scene_info["bricks"]:
            bricks.append(self.GetBound(brick,(25,10)))
        for hard_brick in scene_info["hard_bricks"]:
            hard_bricks.append(self.GetBound(hard_brick,(25,10)))
            
        balls=[]
        runframe =1
        while True:
            points = []
            points.append( self.GetCross(form,ball,speed,'form',0))
            i=0
            for brick in bricks:
                if brick[0]!=None:
                    points.append( self.GetCross(brick,ball,speed,'bricks',i))
                i+=1
            i=0
            for hard_brick in hard_bricks:
                if hard_brick[0]!=None:
                    points.append( self.GetCross(hard_brick,ball,speed,'hard_bricks',i))
                i+=1
                        
            lens = []
            for point in points:
                lens.append(point[1])
                
            Min = min(lens)
            index = lens.index(Min)
            if points[index][4] == 'invx':
                speed = (-speed[0],speed[1])
            elif points[index][4] == 'invy':
                speed = (speed[0],-speed[1])
            
            if points[index][0][0] != None:
                balls.append(points[index][0])
                ball = points[index][0]
                
            else:
                ball =(100,400)
                break
            
            if points[index][2]=='bricks':
                bricks.remove(bricks[points[index][3]])
            elif points[index][2]=='hard_bricks':
                bricks.append((hard_bricks[points[index][3]]))
                hard_bricks.remove((hard_bricks[points[index][3]]))
                
            if ball[1] >=397.5:
                break
            runframe+=1
            if runframe >=1000: # timeout
                break
            
        string = 'runframe '+str(runframe)+' ball '+str(ball)+' vel '+str(speed)
        # string+=' balls '
        # for ball in balls:
        #     string+=' '+str(ball)
        
        Error = ball[0] - real[0]
        
        if not self.ball_served:
            if abs(Error / runframe) > 5: #趕不上
                if Error > 0.5:
                    command = "MOVE_RIGHT"
                elif Error < -0.5:
                    command = "MOVE_LEFT"
                else:
                    command = "NONE"
            else:
                self.ball_served = True
                command = "SERVE_TO_LEFT"
        else:
            if Error > 0.5:
                command = "MOVE_RIGHT"
            elif Error < -0.5:
                command = "MOVE_LEFT"
            else:
                if ball[1] >= 392.5 and len(self.ballvel) >= 1:
                    if  self.ballvel[-1][0] >= 7:
                        command = "MOVE_LEFT"
                    elif self.ballvel[-1][0] <= -7:
                        command = "MOVE_RIGHT"
                    else:
                        command = "NONE"
                else:
                    command = "NONE"
        

        if len(self.ballpos)>=1: 
            tmp =(scene_info["ball"][0] - self.ballpos[-1][0],scene_info["ball"][1] - self.ballpos[-1][1])
            sp =tmp[0]*tmp[0]+tmp[1]*tmp[1];
            if sp >= 49:
                self.ballvel.append(tmp)
            
        self.ballpos.append(scene_info["ball"])
        return command,string

    def reset(self):
        """
        Reset the status
        """
        self.ball_served = False
        
    def GetBound(self,pos=(0,0),size=(5,5),helf_size=(2.5,2.5)):
        TopLeft =(pos[0]-helf_size[0],pos[1]-helf_size[1])
        TopRight =(pos[0]+size[0]+helf_size[0],pos[1]-helf_size[1])
        BottomLeft =(pos[0]-helf_size[0],pos[1]+size[1]+helf_size[1])
        BottomRight =(pos[0]+size[0]+helf_size[0],pos[1]+size[1]+helf_size[1])
        bound =[TopLeft,TopRight,BottomLeft,BottomRight]
        return bound
    
    def GetCenter(self,pos=(0,0),size=(5,5)):
        center =(pos[0]+0.5*size[0],pos[1]+0.5*size[1])
        return center
    
    def GetCross(self,bound,pos,vel,name,num):
        TopLeft = bound[0]
        BottomRight = bound[3]
        
        if vel[0]!=0:
            rate =vel[1]/vel[0]
        else:
            rate =vel[1]/0.0001
            
        b =pos[1]-rate*pos[0]
        
        inv =[]
        Lines=[]
        #L1 [TL,TR]
        y = TopLeft[1]
        if rate==0:
            x = (( y - b ) / 0.0001)
        else:
            x = (( y - b ) / rate)
        if x >= TopLeft[0] and x <= BottomRight[0]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0:  
                Lines.append((x,y))
                inv.append('invy')
        #L2 [BL,BR]
        y = BottomRight[1]
        if rate==0:
            x = (( y - b ) / 0.0001)
        else:
            x = (( y - b ) / rate)
        if x >= TopLeft[0] and x <= BottomRight[0]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invy')
        #L3 [TL,BL]
        x = TopLeft[0]
        y = rate * x + b
        if y >= TopLeft[1] and y <= BottomRight[1]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invx')
        #L4 [TR,BR]
        x = BottomRight[0]
        y = rate * x + b
        if y >= TopLeft[1] and y <= BottomRight[1]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invx')
        
        if len(Lines) ==0:
            return (None,None),99999999,name,num,'None'
        
        lens=[]
        for line in Lines:
            Len =pow( pos[0]-line[0],2)+pow( pos[1]-line[1],2)
            if Len!=0:
                lens.append(Len)
        
        if len(lens) ==0:
            return (None,None),99999999,name,num,'None'
        
        Min =min(lens)
        index = lens.index(Min)
        return Lines[index],Min,name,num,inv[index]
        