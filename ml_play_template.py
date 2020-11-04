"""
The template of the main script of the machine learning process
"""

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
        
        回傳的第二個位置用來放訊息
        """
        # Make the caller to invoke `reset()` for the next round.
        if (scene_info["status"] == "GAME_OVER" or scene_info["status"] == "GAME_PASS"):
            self.reset()
            return "RESET",''
        
        #scene_info["ball"] # 5 * 5
        #scene_info["platform"] # 40 * 5
        #scene_info["bricks"] # 25 * 10
        #scene_info["hard_bricks"] # 25 * 10
        
        ball = self.GetCenter(scene_info["ball"],(5,5))     #得到球的中心座標
        real = self.GetCenter(scene_info["platform"],(40,5))#得到板子的中心座標
        form = self.GetBound((0,0),(200,400),(-2.5,-2.5))   #得到視窗向內膨脹的邊界
        
        if len(self.ballvel)>=1: 
            speed = self.ballvel[-1]
        else:
            speed =(-7,-7) #初始假設的球速
        
        bricks =[]
        hard_bricks =[]
        for brick in scene_info["bricks"]:
            bricks.append(self.GetBound(brick,(25,10)))     #得到軟磚膨脹的邊界
        for hard_brick in scene_info["hard_bricks"]:
            hard_bricks.append(self.GetBound(hard_brick,(25,10))) #得到硬磚膨脹的邊界
        
        
        
        #搜尋球的落點直到Timeout或找到落點
        balls=[]
        runframe =1
        while True:
            points = []
            points.append( self.GetCross(form,ball,speed,'form',0))#掃描邊框的碰撞點
            i=0
            for brick in bricks:
                if brick[0]!=None:
                    points.append( self.GetCross(brick,ball,speed,'bricks',i))#掃描軟磚的碰撞點
                i+=1
            i=0
            for hard_brick in hard_bricks:
                if hard_brick[0]!=None:
                    points.append( self.GetCross(hard_brick,ball,speed,'hard_bricks',i))#掃描硬磚的碰撞點
                i+=1
                    
            #找出最近的碰撞點 
            lens = []
            for point in points:    
                lens.append(point[1])
            Min = min(lens)
            index = lens.index(Min)
            
            #判斷反射面反射速度
            if points[index][4] == 'invx':
                speed = (-speed[0],speed[1])
            elif points[index][4] == 'invy':
                speed = (speed[0],-speed[1])
            
            
            #更新球的位置到碰撞點
            if points[index][0][0] != None:
                balls.append(points[index][0])
                ball = points[index][0]
            else: 
                ball =(100,400) #沒找到碰撞點就假裝球在中線
                break
            
            #碰到軟磚就刪除它
            #若是硬磚就把它變軟磚，球速快的話直接刪除
            if points[index][2]=='bricks':
                bricks.remove(bricks[points[index][3]])
            elif points[index][2]=='hard_bricks':
                sp = speed[0] * speed[0] + speed[1] * speed[1]
                if sp <= 49*2:
                    bricks.append((hard_bricks[points[index][3]]))
                    hard_bricks.remove((hard_bricks[points[index][3]]))
                else:
                    hard_bricks.remove((hard_bricks[points[index][3]]))
                
            #球回到板子高度就跳離
            if ball[1] >=397.5:
                break
            #記錄迴圈次數
            runframe+=1
            if runframe >=1000: # timeout
                break
            
        #記錄用   
        string = 'runframe '+str(runframe)+' ball '+str(ball)+' vel '+str(speed)
        # string+=' balls '
        # for ball in balls:
        #     string+=' '+str(ball)
        
        
        
        Error = ball[0] - real[0]         #追隨誤差  值越大要右移，越小要左移 
        
        if not self.ball_served:          #還沒開球時
            if abs(Error / runframe) > 5: #趕不上所以要移動
                if Error > 0.5:
                    command = "MOVE_RIGHT"
                elif Error < -0.5:
                    command = "MOVE_LEFT"
                else:
                    command = "NONE"
            else:                         #趕得上就直接開球
                self.ball_served = True
                command = "SERVE_TO_LEFT"
        else:                             #已經開球
            if Error > 0.5:
                command = "MOVE_RIGHT"
            elif Error < -0.5:
                command = "MOVE_LEFT"
            else:                         #確定不會漏接就補切球
                if ball[1] >= 392.5 and len(self.ballvel) >= 1:
                    if  self.ballvel[-1][0] >= 7:
                        command = "MOVE_LEFT"
                    elif self.ballvel[-1][0] <= -7:
                        command = "MOVE_RIGHT"
                    else:
                        command = "NONE"
                else:                     #還沒到切球時機就等待
                    command = "NONE"
        
        #記錄球速
        if len(self.ballpos)>=1: 
            tmp =(scene_info["ball"][0] - self.ballpos[-1][0],scene_info["ball"][1] - self.ballpos[-1][1])
            sp =tmp[0]*tmp[0]+tmp[1]*tmp[1];
            if sp >= 49:  #球速要合理才紀錄 過濾反彈瞬間不穩定的速度
                self.ballvel.append(tmp)
        #紀錄球的位置
        self.ballpos.append(scene_info["ball"])
        return command,string

    def reset(self):
        """
        Reset the status
        """
        self.ball_served = False
        self.ballpos =[]
        self.ballvel =[]
        
    def GetBound(self,pos=(0,0),size=(5,5),helf_size=(2.5,2.5)):
        """
        得到膨脹後的邊界
        pos       : 物體的左上角座標
        size      : 物體大小
        helf_size : 碰撞物(球本人)一半的大小，也可以是負的表示向內膨脹
        """
        TopLeft     = ( pos[0] - helf_size[0],           pos[1] - helf_size[1] )
        TopRight    = ( pos[0] + size[0] + helf_size[0], pos[1] - helf_size[1] )
        BottomLeft  = ( pos[0] - helf_size[0],           pos[1] + size[1] + helf_size[1] )
        BottomRight = ( pos[0] + size[0] + helf_size[0], pos[1] + size[1] + helf_size[1] )
        bound = [ TopLeft, TopRight, BottomLeft, BottomRight ]
        return bound
    
    def GetCenter(self,pos=(0,0),size=(5,5)):
        """
        得到物體的中心點座標
        """
        center = ( pos[0] + 0.5 * size[0], pos[1] + 0.5 * size[1] ) 
        return center
    
    def GetCross(self,bound,pos,vel,name,num):
        """
        得到物體邊界與球的交點(碰撞點)
        bound : 物體的邊界
        pos   : 球的座標(中心)
        vel   : 球的速度
        name  : 物體的名稱(可能是軟磚、硬磚、邊框)
        num   : 物體的編號(索引)
        
        
        return :
            Lines[index],    碰撞邊界線上的交點座標 ( 沒撞到就給 ( None, None ) )
            Min,             球到碰撞點的最小距離 ( 沒有的話就給一個很大的值 )
            name,            物體的名稱(可能是軟磚、硬磚、邊框)
            num,             物體的編號(索引)
            inv[index]       決定球的反射方向 'invx' 反射x 
                                             'invy' 反射y
                                             'None' 無反射
        
        """
        TopLeft = bound[0]
        BottomRight = bound[3]
        
        
        #利用球座標與速度建立球的運動直線方程式 y = rate * x + b
        if vel[0]!=0:
            rate =vel[1]/vel[0] # rate
        else:
            rate =vel[1]/0.0001 # 垂直線
        b =pos[1]-rate*pos[0]
        
        inv =[]
        Lines=[]
        #L1 [TL,TR] 上邊界
        y = TopLeft[1]
        if rate==0:
            x = (( y - b ) / 0.0001)
        else:
            x = (( y - b ) / rate) #求出與上邊界的碰撞座標
        if x >= TopLeft[0] and x <= BottomRight[0]: #判斷碰撞點是否在閉區間內
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0:  #判斷碰撞點是否在球的前進方向
                Lines.append((x,y))
                inv.append('invy')
                
        #L2 [BL,BR] 下邊界
        y = BottomRight[1]
        if rate==0:
            x = (( y - b ) / 0.0001)
        else:
            x = (( y - b ) / rate)
        if x >= TopLeft[0] and x <= BottomRight[0]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invy')
                
        #L3 [TL,BL] 左邊界
        x = TopLeft[0]
        y = rate * x + b  #求出與左邊界的碰撞座標
        if y >= TopLeft[1] and y <= BottomRight[1]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invx')
                
        #L4 [TR,BR] 右邊界
        x = BottomRight[0]
        y = rate * x + b
        if y >= TopLeft[1] and y <= BottomRight[1]:
            if (x-pos[0])*vel[0] >=0 and (y-pos[1])*vel[1] >=0: 
                Lines.append((x,y))
                inv.append('invx')
        
        #沒撞到
        if len(Lines) ==0:
            return (None,None),99999999,name,num,'None'
        
        #有撞到 且碰撞點不在球的當前座標上
        lens=[]
        for line in Lines:
            Len =pow( pos[0]-line[0],2)+pow( pos[1]-line[1],2)
            if Len!=0:           
                lens.append(Len)
        #有撞到 但沒有符合條件
        if len(lens) ==0:
            return (None,None),99999999,name,num,'None'
        
        #找出離球最近的碰撞點與索引
        Min =min(lens)
        index = lens.index(Min)
        return Lines[index],Min,name,num,inv[index]
        